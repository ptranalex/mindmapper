"""Main orchestration for JSON-based roadmap scraping."""

import logging
from typing import List, Dict, Optional
from .github_fetcher import GitHubFetcher
from .json_parser import RoadmapParser
from .export import CSVExporter

logger = logging.getLogger(__name__)


class JSONRoadmapScraper:
    """Orchestrates JSON-based roadmap scraping."""
    
    def __init__(self, roadmap_name: str = "engineering-manager", output_path: Optional[str] = None) -> None:
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
    
    def scrape(self) -> Optional[str]:
        """Execute the scraping process.
        
        Returns:
            Path to generated CSV file, or None if export failed
        """
        logger.info("=" * 60)
        logger.info("Starting JSON-based roadmap scraping")
        logger.info(f"Roadmap: {self.roadmap_name}")
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
        
        # Phase 5: Export to CSV
        logger.info("\n" + "=" * 60)
        logger.info("Phase 5: Exporting to CSV")
        logger.info("=" * 60)
        csv_path = self.exporter.export(data_rows, self.output_path, self.roadmap_name)
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total topics found: {len(topics)}")
        logger.info(f"Successfully extracted: {len(data_rows)}/{len(topics)}")
        logger.info(f"Success rate: {len(data_rows)/len(topics)*100:.1f}%")
        logger.info(f"Output file: {csv_path}")
        logger.info("=" * 60)
        
        return csv_path
    
    def _process_topics_with_cache(self, topics: List[Dict], content_cache: Dict[str, str]) -> List[Dict[str, str]]:
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
            topic_label = topic['label']
            topic_id = topic['id']
            
            logger.info(f"Processing topic {i}/{total}: {topic_label}")
            
            # Construct filename key (same as fetch_content_file logic)
            slug = self.fetcher._slugify(topic_label)
            filename_key = f"{slug}@{topic_id}"
            
            # Look up content in cache (instant, in-memory)
            content = content_cache.get(filename_key)
            
            # Use detected hierarchy from topic
            category = topic.get('category', self.parser.category)
            subcategory = topic.get('subcategory', '')
            
            if content:
                # Parse content
                parsed = self.parser.parse_content(content)
                
                # Format row
                row = self.exporter.format_row(
                    category=category,
                    subcategory=subcategory,
                    topic=topic_label,
                    description=parsed['description'],
                    resources=parsed['resources']
                )
                data_rows.append(row)
                logger.info(f"  ✓ Extracted successfully (category: {category}, subcategory: {subcategory or 'None'})")
            else:
                # Create row without content
                row = self.exporter.format_row(
                    category=category,
                    subcategory=subcategory,
                    topic=topic_label,
                    description="",
                    resources=""
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
            topic_label = topic['label']
            topic_id = topic['id']
            
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
                    description=parsed['description'],
                    resources=parsed['resources']
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
                    resources=""
                )
                data_rows.append(row)
                logger.info(f"  ⚠ No content file found (added with empty description)")
        
        return data_rows

