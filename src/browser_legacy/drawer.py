"""Drawer interaction and content extraction."""

import logging
import random
from typing import Optional, Dict, List
from playwright.sync_api import Page, ElementHandle, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class DrawerExtractor:
    """Extracts content from roadmap node drawers."""
    
    # Drawer container selectors to try
    DRAWER_SELECTORS = [
        '[role="dialog"]',
        'aside[aria-modal="true"]',
        '[class*="drawer"]',
        '[class*="modal"]',
        '[class*="sidebar"]',
    ]
    
    # Close button selectors
    CLOSE_SELECTORS = [
        'button[aria-label="Close"]',
        'button[aria-label="close"]',
        'button:has-text("×")',
        'button:has-text("Close")',
        '[class*="close"]',
    ]
    
    DRAWER_TIMEOUT = 5000  # 5 seconds
    
    def __init__(self, page: Page, delay_ms: int = 500):
        """Initialize drawer extractor.
        
        Args:
            page: Playwright page object
            delay_ms: Base delay between actions in milliseconds
        """
        self.page = page
        self.delay_ms = delay_ms
    
    def extract_from_node(self, element: ElementHandle, node_text: str) -> Optional[Dict[str, str]]:
        """Extract content by clicking a node and reading its drawer.
        
        Args:
            element: The node element to click
            node_text: Text of the node (for fallback and logging)
        
        Returns:
            Dict with 'topic', 'description', 'resources' keys, or None if failed
        """
        try:
            # Scroll element into view
            element.scroll_into_view_if_needed()
            self.page.wait_for_timeout(200)
            
            # Click the node
            element.click(timeout=3000)
            
            # Add jittered delay
            delay = self._get_jittered_delay()
            self.page.wait_for_timeout(delay)
            
            # Wait for drawer to appear
            drawer = self._wait_for_drawer()
            if not drawer:
                logger.warning(f"Drawer did not appear for node: {node_text}")
                return None
            
            # Extract content
            topic = self._extract_topic(drawer, node_text)
            description = self._extract_description(drawer)
            resources = self._extract_resources(drawer)
            
            # Close drawer
            self._close_drawer()
            
            return {
                'topic': topic,
                'description': description,
                'resources': resources
            }
        
        except Exception as e:
            logger.warning(f"Failed to extract from node '{node_text}': {e}")
            # Try to close any open drawer before continuing
            self._close_drawer()
            return None
    
    def _wait_for_drawer(self) -> Optional[ElementHandle]:
        """Wait for drawer to appear using multiple selectors.
        
        Returns:
            Drawer element handle or None if not found
        """
        for selector in self.DRAWER_SELECTORS:
            try:
                self.page.wait_for_selector(
                    selector, 
                    timeout=self.DRAWER_TIMEOUT, 
                    state='visible'
                )
                drawer = self.page.query_selector(selector)
                if drawer:
                    logger.debug(f"Drawer found with selector: {selector}")
                    return drawer
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue
        
        return None
    
    def _extract_topic(self, drawer: ElementHandle, fallback: str) -> str:
        """Extract topic title from drawer.
        
        Args:
            drawer: Drawer element
            fallback: Fallback text if extraction fails
        
        Returns:
            Topic title string
        """
        # Try to find heading in drawer
        heading_selectors = ['h1', 'h2', 'h3', '[role="heading"]']
        
        for selector in heading_selectors:
            try:
                heading = drawer.query_selector(selector)
                if heading:
                    text = heading.text_content()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        
        # Fallback to node text
        return fallback
    
    def _extract_description(self, drawer: ElementHandle) -> str:
        """Extract description from drawer.
        
        Args:
            drawer: Drawer element
        
        Returns:
            Description text (may be empty)
        """
        try:
            # Look for paragraphs in the drawer
            paragraphs = drawer.query_selector_all('p')
            
            descriptions = []
            for p in paragraphs:
                text = p.text_content()
                if text and text.strip():
                    descriptions.append(text.strip())
            
            # Join all paragraphs with space
            return ' '.join(descriptions)
        
        except Exception as e:
            logger.debug(f"Error extracting description: {e}")
            return ""
    
    def _extract_resources(self, drawer: ElementHandle) -> str:
        """Extract resources from drawer.
        
        Args:
            drawer: Drawer element
        
        Returns:
            Pipe-separated URLs
        """
        try:
            # First, try to find and click a "Resources" tab/button
            self._try_click_resources_tab()
            
            # Give time for resources to load
            self.page.wait_for_timeout(500)
            
            # Collect all links in the drawer
            links = drawer.query_selector_all('a[href]')
            
            urls = []
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and not href.startswith('#'):
                        # Make absolute URLs
                        if href.startswith('http'):
                            urls.append(href)
                        elif href.startswith('/'):
                            # Relative URL - prepend base
                            base_url = self.page.url.split('/')[0:3]  # protocol://domain
                            urls.append(''.join(base_url) + href)
                except Exception:
                    continue
            
            # Deduplicate and join with pipe
            unique_urls = list(dict.fromkeys(urls))  # Preserve order
            return '|'.join(unique_urls)
        
        except Exception as e:
            logger.debug(f"Error extracting resources: {e}")
            return ""
    
    def _try_click_resources_tab(self):
        """Try to click a Resources tab/button if it exists."""
        resources_selectors = [
            'button:has-text("Resources")',
            'a:has-text("Resources")',
            '[role="tab"]:has-text("Resources")',
            'div:has-text("Resources")',
        ]
        
        for selector in resources_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=500):
                    element.click(timeout=500)
                    logger.debug("Clicked Resources tab")
                    return
            except Exception:
                continue
    
    def _close_drawer(self):
        """Close the drawer using various methods."""
        # Method 1: Try close button
        for selector in self.CLOSE_SELECTORS:
            try:
                button = self.page.locator(selector).first
                if button.is_visible(timeout=500):
                    button.click(timeout=500)
                    self.page.wait_for_timeout(300)
                    logger.debug(f"Closed drawer with selector: {selector}")
                    return
            except Exception:
                continue
        
        # Method 2: Try ESC key
        try:
            self.page.keyboard.press('Escape')
            self.page.wait_for_timeout(300)
            logger.debug("Closed drawer with ESC key")
            return
        except Exception:
            pass
        
        # Method 3: Click backdrop (if modal)
        try:
            # Click outside the drawer (top-left corner)
            self.page.mouse.click(10, 10)
            self.page.wait_for_timeout(300)
            logger.debug("Closed drawer by clicking backdrop")
        except Exception:
            pass
    
    def _get_jittered_delay(self) -> int:
        """Get delay with random jitter (±20%).
        
        Returns:
            Delay in milliseconds
        """
        jitter = random.uniform(0.8, 1.2)
        return int(self.delay_ms * jitter)

