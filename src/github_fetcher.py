"""GitHub content fetcher for roadmap data."""

import logging
import json
import re
import sys
from typing import Dict, Optional, List, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

# Feature detection for parallel fetching  
if sys.version_info >= (3, 14):
    # Check if GIL is disabled (free-threading mode)
    PARALLEL_AVAILABLE = (
        not hasattr(sys, '_is_gil_enabled') or 
        not getattr(sys, '_is_gil_enabled', lambda: True)()
    )
else:
    PARALLEL_AVAILABLE = False

ASYNC_AVAILABLE = True
try:
    import aiohttp
except ImportError:
    ASYNC_AVAILABLE = False
    logger.debug("aiohttp not available, async fetching disabled")


class GitHubFetcher:
    """Fetches roadmap data from GitHub repository."""
    
    BASE_URL = "https://raw.githubusercontent.com/kamranahmedse/developer-roadmap/master/src/data/roadmaps"
    API_URL = "https://api.github.com/repos/kamranahmedse/developer-roadmap/contents/src/data/roadmaps"
    
    def __init__(self, roadmap_name: str = "engineering-manager") -> None:
        """Initialize fetcher.
        
        Args:
            roadmap_name: Name of the roadmap to fetch
        """
        self.roadmap_name = roadmap_name
        self.base_roadmap_url = f"{self.BASE_URL}/{roadmap_name}"
    
    def fetch_roadmap_json(self) -> Dict[str, Any]:
        """Fetch the main roadmap JSON file.
        
        Returns:
            Parsed JSON data as dictionary
        
        Raises:
            Exception: If download fails
        """
        url = f"{self.base_roadmap_url}/{self.roadmap_name}.json"
        logger.info(f"Fetching roadmap JSON from {url}")
        
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=30) as response:
                data: Dict[str, Any] = json.loads(response.read().decode('utf-8'))
            
            logger.info(f"Successfully fetched JSON with {len(data.get('nodes', []))} nodes")
            return data
        
        except (URLError, HTTPError) as e:
            logger.error(f"Failed to fetch roadmap JSON: {e}")
            raise Exception(f"Could not download roadmap data: {e}")
    
    def fetch_content_file(self, topic_label: str, node_id: str) -> Optional[str]:
        """Fetch content markdown file for a topic.
        
        Args:
            topic_label: The topic label/name
            node_id: The node ID from JSON
        
        Returns:
            Markdown content as string, or None if not found
        """
        # Create filename: slugify label + @ + node_id + .md
        slug = self._slugify(topic_label)
        filename = f"{slug}@{node_id}.md"
        url = f"{self.base_roadmap_url}/content/{filename}"
        
        logger.debug(f"Fetching content: {filename}")
        
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=10) as response:
                content: str = response.read().decode('utf-8')
            return content
        
        except HTTPError as e:
            if e.code == 404:
                logger.debug(f"Content file not found: {filename}")
                return None
            logger.warning(f"HTTP error fetching {filename}: {e}")
            return None
        
        except Exception as e:
            logger.warning(f"Error fetching {filename}: {e}")
            return None
    
    def fetch_all_content_files(self) -> Dict[str, str]:
        """Fetch all markdown files from content directory at once.
        
        Uses GitHub API to list directory contents, then fetches all
        content files using async parallelization if available.
        
        Returns:
            Dict mapping filename (without .md) -> content string
            
        Raises:
            Exception: If API call or content fetching fails
        """
        logger.info("Fetching all content files in bulk...")
        
        # Use GitHub API to list directory contents
        api_url = f"{self.API_URL}/{self.roadmap_name}/content"
        logger.debug(f"Listing directory: {api_url}")
        
        try:
            req = Request(api_url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/vnd.github.v3+json'
            })
            with urlopen(req, timeout=30) as response:
                files_list = json.loads(response.read().decode('utf-8'))
            
            logger.info(f"Found {len(files_list)} files in content directory")
            
            # Choose fetching strategy based on available features
            if PARALLEL_AVAILABLE:
                # Python 3.14+ with free-threading - use ThreadPoolExecutor
                logger.info("Using free-threaded parallel fetching (Python 3.14+)")
                from .parallel_fetcher import fetch_all_parallel_sync
                return fetch_all_parallel_sync(files_list, max_workers=20)
            elif ASYNC_AVAILABLE:
                # Python 3.9-3.13 with aiohttp - use async
                logger.info("Using async parallel fetching (aiohttp)")
                from .async_fetcher import fetch_all_async_sync
                return fetch_all_async_sync(files_list, max_concurrent=20)
            else:
                # Fallback to sequential
                logger.info("Using sequential fetching (no parallelization available)")
                return self._fetch_all_sequential(files_list)
            
        except (URLError, HTTPError) as e:
            logger.error(f"Failed to list content directory: {e}")
            raise Exception(f"Could not list content files: {e}")
    
    def _fetch_all_sequential(self, files_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """Fetch all content files sequentially (fallback method).
        
        Args:
            files_list: List of file info dicts from GitHub API
        
        Returns:
            Dict mapping filename (without .md) -> content string
        """
        content_cache: Dict[str, str] = {}
        successful = 0
        failed = 0
        
        for file_info in files_list:
            filename = file_info.get('name', '')
            
            # Only process .md files
            if not filename.endswith('.md'):
                continue
            
            # Get download URL from API response
            download_url = file_info.get('download_url')
            if not download_url:
                logger.warning(f"No download URL for {filename}")
                failed += 1
                continue
            
            # Fetch content
            try:
                req = Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=10) as response:
                    content: str = response.read().decode('utf-8')
                
                # Store with filename as key (without .md extension)
                key = filename[:-3]  # Remove .md
                content_cache[key] = content
                successful += 1
                
            except Exception as e:
                logger.warning(f"Failed to fetch {filename}: {e}")
                failed += 1
        
        logger.info(f"Sequential fetch complete: {successful} successful, {failed} failed")
        return content_cache
    
    def list_available_roadmaps(self) -> List[str]:
        """Fetch list of all available roadmaps from GitHub.
        
        Returns:
            Sorted list of roadmap names (e.g., ['frontend', 'backend', 'devops'])
            
        Raises:
            Exception: If API call fails
        """
        logger.info("Fetching list of available roadmaps...")
        
        try:
            req = Request(self.API_URL, headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/vnd.github.v3+json'
            })
            with urlopen(req, timeout=30) as response:
                items = json.loads(response.read().decode('utf-8'))
            
            # Filter for directories only
            roadmaps = []
            for item in items:
                if item.get('type') == 'dir':
                    roadmaps.append(item.get('name', ''))
            
            roadmaps.sort()
            logger.info(f"Found {len(roadmaps)} available roadmaps")
            return roadmaps
            
        except (URLError, HTTPError) as e:
            logger.error(f"Failed to list roadmaps: {e}")
            raise Exception(f"Could not list available roadmaps: {e}")
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug.
        
        Args:
            text: Text to slugify
        
        Returns:
            Slugified string
        """
        # Convert to lowercase
        text = text.lower()
        # Replace spaces and special chars with hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        text = re.sub(r'^-+|-+$', '', text)
        return text

