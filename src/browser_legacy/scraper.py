"""Main orchestration logic for roadmap scraping."""

import logging
from typing import List, Dict, Optional
from .browser import BrowserManager
from .nodes import NodeExtractor, RoadmapNode
from .drawer import DrawerExtractor
from .export import CSVExporter

logger = logging.getLogger(__name__)


class RoadmapScraper:
    """Orchestrates the scraping process."""
    
    def __init__(self, url: str, output_path: Optional[str] = None, 
                 delay_ms: int = 500, headless: bool = False):
        """Initialize scraper.
        
        Args:
            url: Target URL to scrape
            output_path: Optional output CSV path
            delay_ms: Delay between drawer interactions
            headless: Run browser in headless mode
        """
        self.url = url
        self.output_path = output_path
        self.delay_ms = delay_ms
        self.headless = headless
    
    def scrape(self) -> str:
        """Execute the scraping process.
        
        Returns:
            Path to generated CSV file
        """
        logger.info("=" * 60)
        logger.info("Starting roadmap scraping process")
        logger.info(f"URL: {self.url}")
        logger.info(f"Headless: {self.headless}")
        logger.info(f"Delay: {self.delay_ms}ms")
        logger.info("=" * 60)
        
        with BrowserManager(headless=self.headless) as browser:
            # Navigate and prepare page
            browser.navigate_to(self.url)
            browser.dismiss_overlays()
            browser.wait_for_roadmap_canvas()
            
            # Extract nodes
            logger.info("\n" + "=" * 60)
            logger.info("Phase 1: Node Extraction")
            logger.info("=" * 60)
            extractor = NodeExtractor(browser.page)
            nodes = extractor.extract_all_nodes()
            
            # Infer hierarchy
            logger.info("\n" + "=" * 60)
            logger.info("Phase 2: Hierarchy Inference")
            logger.info("=" * 60)
            nodes = extractor.infer_hierarchy(nodes)
            
            # Extract from drawers (only leaf nodes)
            logger.info("\n" + "=" * 60)
            logger.info("Phase 3: Drawer Content Extraction")
            logger.info("=" * 60)
            leaf_nodes = [n for n in nodes if n.node_type == 'leaf']
            data = self._extract_drawer_content(browser.page, leaf_nodes)
            
            # Export to CSV
            logger.info("\n" + "=" * 60)
            logger.info("Phase 4: Export to CSV")
            logger.info("=" * 60)
            exporter = CSVExporter()
            csv_path = exporter.export(data, self.output_path)
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total nodes found: {len(nodes)}")
        logger.info(f"Leaf nodes (topics): {len(leaf_nodes)}")
        logger.info(f"Successfully extracted: {len(data)}/{len(leaf_nodes)}")
        logger.info(f"Success rate: {len(data)/len(leaf_nodes)*100:.1f}%")
        logger.info(f"Output file: {csv_path}")
        logger.info("=" * 60)
        
        return csv_path
    
    def _extract_drawer_content(self, page, leaf_nodes: List[RoadmapNode]) -> List[Dict[str, str]]:
        """Extract content from all leaf node drawers.
        
        Args:
            page: Playwright page object
            leaf_nodes: List of leaf nodes to process
        
        Returns:
            List of formatted data rows
        """
        drawer_extractor = DrawerExtractor(page, delay_ms=self.delay_ms)
        exporter = CSVExporter()
        
        data = []
        total = len(leaf_nodes)
        
        for i, node in enumerate(leaf_nodes, 1):
            logger.info(f"Processing node {i}/{total}: {node.text}")
            
            drawer_content = drawer_extractor.extract_from_node(
                node.element, 
                node.text
            )
            
            if drawer_content:
                # Format row
                row = exporter.format_row(
                    category=node.category,
                    subcategory=node.subcategory,
                    topic=drawer_content['topic'],
                    description=drawer_content['description'],
                    resources=drawer_content['resources']
                )
                data.append(row)
                logger.info(f"  ✓ Extracted successfully")
            else:
                logger.warning(f"  ✗ Failed to extract content")
        
        return data

