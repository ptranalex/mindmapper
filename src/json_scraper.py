"""Main orchestration for JSON-based roadmap scraping."""

import logging
from typing import List, Dict, Optional
from .github_fetcher import GitHubFetcher
from .json_parser import RoadmapParser
from .export import CSVExporter
from .enrichment import EnrichmentCache, GeminiEnricher

logger = logging.getLogger(__name__)


class JSONRoadmapScraper:
    """Orchestrates JSON-based roadmap scraping."""

    def __init__(
        self,
        roadmap_name: str = "engineering-manager",
        output_path: Optional[str] = None,
    ) -> None:
        """Initialize scraper.

        Args:
            roadmap_name: Name of the roadmap to scrape
            output_path: Optional output CSV path
        """
        self.roadmap_name = roadmap_name
        self.output_path = output_path
        self.fetcher = GitHubFetcher(roadmap_name)
        self.parser = RoadmapParser(roadmap_name)
        self.exporter = CSVExporter()

    def scrape(
        self, enrich: bool = False, gemini_api_key: Optional[str] = None
    ) -> Optional[str]:
        """Execute the scraping process.

        Args:
            enrich: Whether to enrich CSV with AI-generated summaries
            gemini_api_key: Google Gemini API key (required if enrich=True)

        Returns:
            Path to generated CSV file, or None if export failed

        Raises:
            ValueError: If enrich=True but no API key provided
        """
        logger.info("=" * 60)
        logger.info("Starting JSON-based roadmap scraping")
        logger.info(f"Roadmap: {self.roadmap_name}")
        logger.info(f"Enrichment: {'Enabled' if enrich else 'Disabled'}")
        logger.info("=" * 60)

        # Phase 1: Fetch roadmap JSON
        logger.info("\n" + "=" * 60)
        logger.info("Phase 1: Fetching Roadmap JSON")
        logger.info("=" * 60)
        roadmap_data = self.fetcher.fetch_roadmap_json()

        # Phase 2: Extract topics
        logger.info("\n" + "=" * 60)
        logger.info("Phase 2: Extracting Topics")
        logger.info("=" * 60)
        topics = self.parser.extract_topics(roadmap_data)

        # Phase 3: BULK fetch all content files ONCE
        logger.info("\n" + "=" * 60)
        logger.info("Phase 3: Bulk Fetching All Content Files")
        logger.info("=" * 60)
        content_cache = self.fetcher.fetch_all_content_files()

        # Phase 4: Process topics using cached content
        logger.info("\n" + "=" * 60)
        logger.info("Phase 4: Processing Topics with Cached Content")
        logger.info("=" * 60)
        data_rows = self._process_topics_with_cache(topics, content_cache)

        # Phase 5: Enrich data (if requested)
        if enrich:
            if not gemini_api_key:
                raise ValueError("Gemini API key required for enrichment")

            logger.info("\n" + "=" * 60)
            logger.info("Phase 5: Enriching with GenAI")
            logger.info("=" * 60)
            data_rows = self._enrich_data(data_rows, gemini_api_key)

        # Phase 6: Export to CSV
        phase_num = 6 if enrich else 5
        logger.info("\n" + "=" * 60)
        logger.info(f"Phase {phase_num}: Exporting to CSV")
        logger.info("=" * 60)
        csv_path = self.exporter.export(data_rows, self.output_path, self.roadmap_name)

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total topics found: {len(topics)}")
        logger.info(f"Successfully extracted: {len(data_rows)}/{len(topics)}")
        logger.info(f"Success rate: {len(data_rows)/len(topics)*100:.1f}%")
        if enrich:
            enriched_count = sum(1 for row in data_rows if row.get("TLDR"))
            logger.info(f"Enriched rows: {enriched_count}/{len(data_rows)}")
        logger.info(f"Output file: {csv_path}")
        logger.info("=" * 60)

        return csv_path

    def _process_topics_with_cache(
        self, topics: List[Dict], content_cache: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Process all topics using bulk-fetched content cache.

        Args:
            topics: List of topic dictionaries
            content_cache: Pre-fetched content dictionary (filename -> content)

        Returns:
            List of formatted data rows for CSV export
        """
        data_rows = []
        total = len(topics)

        for i, topic in enumerate(topics, 1):
            topic_label = topic["label"]
            topic_id = topic["id"]

            logger.info(f"Processing topic {i}/{total}: {topic_label}")

            # Construct filename key (same as fetch_content_file logic)
            slug = self.fetcher._slugify(topic_label)
            filename_key = f"{slug}@{topic_id}"

            # Look up content in cache (instant, in-memory)
            content = content_cache.get(filename_key)

            # Use detected hierarchy from topic
            category = topic.get("category", self.parser.category)
            subcategory = topic.get("subcategory", "")

            if content:
                # Parse content
                parsed = self.parser.parse_content(content)

                # Format row
                row = self.exporter.format_row(
                    category=category,
                    subcategory=subcategory,
                    topic=topic_label,
                    description=parsed["description"],
                    resources=parsed["resources"],
                )
                data_rows.append(row)
                logger.info(
                    f"  ✓ Extracted successfully (category: {category}, subcategory: {subcategory or 'None'})"
                )
            else:
                # Create row without content
                row = self.exporter.format_row(
                    category=category,
                    subcategory=subcategory,
                    topic=topic_label,
                    description="",
                    resources="",
                )
                data_rows.append(row)
                logger.info(f"  ⚠ No content in cache (added with empty description)")

        return data_rows

    def _fetch_topic_content(self, topics: List[Dict]) -> List[Dict[str, str]]:
        """Legacy method: Fetch content for all topics one-by-one.

        DEPRECATED: Use _process_topics_with_cache instead for better performance.

        Args:
            topics: List of topic dictionaries

        Returns:
            List of formatted data rows for CSV export
        """
        data_rows = []
        total = len(topics)

        for i, topic in enumerate(topics, 1):
            topic_label = topic["label"]
            topic_id = topic["id"]

            logger.info(f"Processing topic {i}/{total}: {topic_label}")

            # Fetch content file
            content = self.fetcher.fetch_content_file(topic_label, topic_id)

            if content:
                # Parse content
                parsed = self.parser.parse_content(content)

                # Format row
                row = self.exporter.format_row(
                    category=self.parser.category,
                    subcategory="",  # Flat structure for MVP
                    topic=topic_label,
                    description=parsed["description"],
                    resources=parsed["resources"],
                )
                data_rows.append(row)
                logger.info(f"  ✓ Extracted successfully")
            else:
                # Create row without content
                row = self.exporter.format_row(
                    category=self.parser.category,
                    subcategory="",
                    topic=topic_label,
                    description="",
                    resources="",
                )
                data_rows.append(row)
                logger.info(f"  ⚠ No content file found (added with empty description)")

        return data_rows

    def _enrich_data(
        self, data_rows: List[Dict[str, str]], gemini_api_key: str
    ) -> List[Dict[str, str]]:
        """Enrich data rows with AI-generated TLDR and challenge level.

        Args:
            data_rows: List of data rows to enrich
            gemini_api_key: Google Gemini API key

        Returns:
            Enriched data rows with TLDR and Challenge columns
        """
        # Initialize cache and enricher
        cache = EnrichmentCache()
        enricher = GeminiEnricher(gemini_api_key, cache)

        # Show cache stats
        cache_count, cache_latest = cache.stats()
        if cache_count > 0:
            logger.info(
                f"Cache contains {cache_count} entries (latest: {cache_latest})"
            )
        else:
            logger.info("Cache is empty")

        enriched_rows = []
        total = len(data_rows)
        failed = 0

        for i, row in enumerate(data_rows, 1):
            topic = row["Topic"]
            category = row.get("Category", "")
            subcategory = row.get("Subcategory", "")
            description = row.get("Description", "")

            logger.info(f"\n[{i}/{total}] {topic}")

            try:
                # Enrich the row
                enrichment = enricher.enrich_row(
                    category, subcategory, topic, description
                )

                # Add enrichment to row
                row["TLDR"] = enrichment["tldr"]
                row["Challenge"] = enrichment["challenge"]

                logger.info(f"  TLDR: {enrichment['tldr']}")
                logger.info(f"  Challenge: {enrichment['challenge']}")

            except Exception as e:
                logger.error(f"  ✗ Failed to enrich: {str(e)}")
                # Add empty enrichment for failed rows
                row["TLDR"] = ""
                row["Challenge"] = ""
                failed += 1

            enriched_rows.append(row)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("ENRICHMENT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total rows: {total}")
        logger.info(f"Successfully enriched: {total - failed}")
        logger.info(f"Failed: {failed}")
        if failed > 0:
            logger.warning(f"Success rate: {(total - failed)/total*100:.1f}%")
        else:
            logger.info("Success rate: 100%")
        logger.info("=" * 60)

        return enriched_rows
