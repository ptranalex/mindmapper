"""Async content fetcher for parallel downloads."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class AsyncContentFetcher:
    """Asynchronous content fetcher for parallel downloads."""
    
    def __init__(self, max_concurrent: int = 20) -> None:
        """Initialize with concurrency limit.
        
        Args:
            max_concurrent: Maximum number of concurrent downloads
        """
        self.max_concurrent = max_concurrent
        self.semaphore: Optional[asyncio.Semaphore] = None
    
    async def fetch_all_async(self, files_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """Fetch all content files asynchronously.
        
        Args:
            files_list: List of file info dicts with 'name' and 'download_url'
        
        Returns:
            Dict mapping filename (without .md) -> content
        """
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        content_cache: Dict[str, str] = {}
        successful = 0
        failed = 0
        
        # Filter markdown files
        md_files = [f for f in files_list if f.get('name', '').endswith('.md')]
        
        logger.info(f"Starting async fetch of {len(md_files)} files with {self.max_concurrent} concurrent connections")
        
        # Create session and fetch all files
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_single(session, file_info)
                for file_info in md_files
            ]
            
            # Gather all results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for file_info, result in zip(md_files, results):
                filename = file_info.get('name', '')
                
                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch {filename}: {result}")
                    failed += 1
                elif result and isinstance(result, str):
                    key = filename[:-3]  # Remove .md extension
                    content_cache[key] = result
                    successful += 1
                else:
                    failed += 1
        
        logger.info(f"Async fetch complete: {successful} successful, {failed} failed")
        return content_cache
    
    async def _fetch_single(self, session: aiohttp.ClientSession, file_info: Dict[str, Any]) -> Optional[str]:
        """Fetch a single file asynchronously.
        
        Args:
            session: aiohttp session
            file_info: Dict with 'download_url' key
        
        Returns:
            File content as string, or None if failed
        """
        download_url = file_info.get('download_url')
        if not download_url:
            return None
        
        if self.semaphore is None:
            return None
        
        async with self.semaphore:
            try:
                async with session.get(
                    download_url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        text: str = await response.text()
                        return text
                    else:
                        logger.warning(f"HTTP {response.status} for {download_url}")
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {download_url}")
                return None
            except Exception as e:
                logger.debug(f"Error fetching {download_url}: {e}")
                return None


def fetch_all_async_sync(files_list: List[Dict[str, Any]], max_concurrent: int = 20) -> Dict[str, str]:
    """Synchronous wrapper for async fetching.
    
    This allows the async fetcher to be called from synchronous code.
    
    Args:
        files_list: List of file info dicts
        max_concurrent: Maximum concurrent downloads
    
    Returns:
        Dict mapping filename -> content
    """
    fetcher = AsyncContentFetcher(max_concurrent=max_concurrent)
    
    # Run async code in event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create new loop if one is already running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(fetcher.fetch_all_async(files_list))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(fetcher.fetch_all_async(files_list))

