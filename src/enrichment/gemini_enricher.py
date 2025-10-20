"""Gemini API integration for CSV enrichment."""

import json
import logging
import random
import time
from typing import Dict, List, Tuple

from google import genai  # type: ignore
from google.genai import types, errors  # type: ignore
import requests  # type: ignore

from .cache import EnrichmentCache
from .prompts import (
    build_prompt,
    build_batch_prompt,
    RESPONSE_SCHEMA,
    BATCH_RESPONSE_SCHEMA,
)

logger = logging.getLogger(__name__)


class GeminiEnricher:
    """Enriches CSV rows using Google Gemini API."""

    # Use the latest stable model
    SUPPORTED_MODEL = "gemini-2.5-flash-lite"

    def __init__(self, api_key: str, cache: EnrichmentCache) -> None:
        """Initialize the Gemini enricher.

        Args:
            api_key: Google Gemini API key
            cache: EnrichmentCache instance for caching results

        Raises:
            ValueError: If API key is invalid or client initialization fails
        """
        if not api_key:
            raise ValueError("Gemini API key is required")

        # Initialize the Gemini client
        try:
            self.client = genai.Client(api_key=api_key)
            logger.debug("Initialized Gemini client")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise ValueError(f"Unable to initialize Gemini client: {str(e)}")

        self.model = self.SUPPORTED_MODEL
        self.cache = cache
        self.temperature = 0.0  # Deterministic for consistent caching
        self.last_request_time = 0.0
        self.min_request_interval = 4.0  # 15 RPM = 4s between requests

        logger.info(f"Using Gemini model: {self.model}")

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """Validate Google Gemini API key.

        Args:
            api_key: Gemini API key to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key:
            return False, "API key is empty"

        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            )
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return True, ""
            elif response.status_code == 400:
                error_data = response.json()
                if "error" in error_data and "API key not valid" in error_data.get(
                    "error", {}
                ).get("message", ""):
                    return False, "Invalid API key"
                return False, "Bad request"
            elif response.status_code == 403:
                return False, "API key unauthorized or invalid"
            else:
                error_data = response.json().get("error", {})
                error_msg = error_data.get("message", f"Error {response.status_code}")
                return False, error_msg

        except requests.exceptions.Timeout:
            return False, "Request timed out. Check your network connection"
        except requests.exceptions.ConnectionError:
            return False, "Connection error. Check your network connection"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def enrich_row(
        self, category: str, subcategory: str, topic: str, description: str
    ) -> Dict[str, str]:
        """Enrich a single row with TLDR and challenge level.

        Args:
            category: Category name
            subcategory: Subcategory name
            topic: Topic name
            description: Description text

        Returns:
            Dictionary with 'tldr' and 'challenge' keys
        """
        # Check cache first
        row_hash = self.cache.compute_hash(category, subcategory, topic, description)
        cached = self.cache.get(row_hash)
        if cached:
            logger.info(f"✓ Cache hit for '{topic}'")
            return {"tldr": cached[0], "challenge": cached[1]}

        # Generate with Gemini
        logger.info(f"⚡ Generating enrichment for '{topic}'...")
        result = self._generate_with_retry(category, subcategory, topic, description)

        # Cache result
        self.cache.set(row_hash, result["tldr"], result["challenge"])

        return result

    def _throttle(self) -> None:
        """Implement rate limiting (15 RPM = 4s between requests)."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _generate_enrichment(
        self, category: str, subcategory: str, topic: str, description: str
    ) -> Dict[str, str]:
        """Generate enrichment using Gemini API.

        Args:
            category: Category name
            subcategory: Subcategory name
            topic: Topic name
            description: Description text

        Returns:
            Dictionary with 'tldr' and 'challenge' keys

        Raises:
            Exception: If API call fails
        """
        # Apply rate limiting
        self._throttle()

        # Build prompt
        prompt = build_prompt(category, subcategory, topic, description)

        # Call Gemini with structured output
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=self.temperature,
                ),
            )

            # Parse JSON response
            result: Dict[str, str] = json.loads(response.text)

            # Validate response
            if "tldr" not in result or "challenge" not in result:
                raise ValueError(f"Invalid response structure: {result}")

            if result["challenge"] not in ["practice", "expert"]:
                logger.warning(
                    f"Invalid challenge level '{result['challenge']}', defaulting to 'practice'"
                )
                result["challenge"] = "practice"

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise Exception(f"Invalid JSON response from Gemini: {e}")

    def _generate_with_retry(
        self,
        category: str,
        subcategory: str,
        topic: str,
        description: str,
        max_retries: int = 3,
    ) -> Dict[str, str]:
        """Generate enrichment with retry logic.

        Args:
            category: Category name
            subcategory: Subcategory name
            topic: Topic name
            description: Description text
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with 'tldr' and 'challenge' keys

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                return self._generate_enrichment(
                    category, subcategory, topic, description
                )

            except errors.ClientError as e:
                # Check if it's a rate limit error
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    backoff = (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                    continue
                elif "500" in error_msg or "503" in error_msg:
                    backoff = (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Server error (attempt {attempt + 1}/{max_retries}), retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                    continue
                else:
                    # Don't retry client errors
                    logger.error(f"Client error: {error_msg}")
                    raise

            except Exception as e:
                error_msg = str(e)
                # Check for rate limit or server errors in generic exceptions
                if (
                    "429" in error_msg
                    or "RESOURCE_EXHAUSTED" in error_msg
                    or "quota" in error_msg.lower()
                ):
                    backoff = (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                    continue
                elif "500" in error_msg or "503" in error_msg or "504" in error_msg:
                    backoff = (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Server error (attempt {attempt + 1}/{max_retries}), retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"Error generating enrichment: {error_msg}")
                    raise

        raise Exception(f"Failed to generate enrichment after {max_retries} retries")

    def enrich_batch(self, rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Enrich a batch of rows.

        Args:
            rows: List of row dictionaries (max 20)

        Returns:
            List of enrichment results with 'tldr' and 'challenge'

        Raises:
            ValueError: If batch size exceeds 20 rows
        """
        if len(rows) > 20:
            raise ValueError("Batch size must be ≤20 rows")

        # Build batch prompt
        prompt = build_batch_prompt(rows)

        # Call Gemini with batch response schema
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=BATCH_RESPONSE_SCHEMA,
                temperature=self.temperature,
            ),
        )

        # Parse batch response
        results: List[Dict[str, str]] = json.loads(response.text)

        # Validate response
        if len(results) != len(rows):
            logger.warning(
                f"Batch response length mismatch: expected {len(rows)}, got {len(results)}"
            )

        # Map results by ID
        results_map = {r["id"]: r for r in results}

        # Return in original order
        enrichments = []
        for i in range(len(rows)):
            result = results_map.get(str(i), {"tldr": "", "challenge": "practice"})
            enrichments.append(
                {
                    "tldr": result.get("tldr", ""),
                    "challenge": result.get("challenge", "practice"),
                }
            )

        return enrichments
