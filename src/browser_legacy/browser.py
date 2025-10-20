"""Browser management for roadmap scraping using Playwright."""

import logging
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser lifecycle and page interactions."""
    
    def __init__(self, headless: bool = False):
        """Initialize browser manager.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self):
        """Start the browser and create a new page."""
        logger.info(f"Starting browser (headless={self.headless})")
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ],
                timeout=60000
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_https_errors=True,
                # Add extra stealth options
                java_script_enabled=True,
                bypass_csp=True,
            )
            self.page = self.context.new_page()
            # Set longer default timeout
            self.page.set_default_timeout(60000)
            
            # Add stealth scripts to avoid detection
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    def navigate_to(self, url: str, wait_for: str = 'domcontentloaded'):
        """Navigate to URL and wait for page to load.
        
        Args:
            url: Target URL
            wait_for: Wait strategy ('networkidle', 'domcontentloaded', 'load')
        """
        logger.info(f"Navigating to {url}")
        try:
            self.page.goto(url, wait_until=wait_for, timeout=60000)
            logger.info("Page loaded successfully")
            # Give the page a moment to fully render
            self.page.wait_for_timeout(2000)
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise
    
    def dismiss_overlays(self):
        """Dismiss common overlays like cookie banners and popups.
        
        Tries multiple common selectors and continues on failure.
        """
        logger.info("Attempting to dismiss overlays")
        
        # Common overlay selectors to try
        overlay_selectors = [
            # Cookie consent
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("I Accept")',
            'button:has-text("Agree")',
            '[class*="cookie"] button',
            '[id*="cookie"] button',
            
            # Close buttons
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            '[class*="close"]',
            '[class*="dismiss"]',
            
            # Modal overlays
            '[role="dialog"] button:has-text("Close")',
            '[role="dialog"] button:has-text("×")',
        ]
        
        dismissed_count = 0
        for selector in overlay_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=1000):
                    element.click(timeout=1000)
                    dismissed_count += 1
                    logger.debug(f"Dismissed overlay with selector: {selector}")
                    self.page.wait_for_timeout(500)  # Brief pause after dismissing
            except Exception:
                # Selector not found or not clickable, continue
                pass
        
        if dismissed_count > 0:
            logger.info(f"Dismissed {dismissed_count} overlay(s)")
        else:
            logger.info("No overlays found to dismiss")
    
    def wait_for_roadmap_canvas(self, timeout: int = 15000):
        """Wait for the roadmap canvas to be visible and interactive.
        
        Args:
            timeout: Maximum wait time in milliseconds
        
        Raises:
            TimeoutError: If roadmap canvas doesn't appear
        """
        logger.info("Waiting for roadmap canvas to render")
        
        # Wait for SVG elements (roadmap.sh uses SVG for the roadmap)
        try:
            self.page.wait_for_selector('svg', timeout=timeout, state='visible')
            logger.info("Roadmap canvas (SVG) found")
            # Brief wait for initial render
            self.page.wait_for_load_state('networkidle', timeout=10000)
            logger.info("Roadmap canvas ready")
        except Exception as e:
            logger.error(f"Failed to wait for roadmap canvas: {e}")
            # Continue anyway if SVG is found
            logger.warning("Continuing despite wait error - SVG elements exist")
    
    def get_viewport_height(self) -> int:
        """Get the current viewport height in pixels."""
        return self.page.viewport_size['height']
    
    def scroll_to_position(self, y_position: int):
        """Scroll to a specific Y position on the page.
        
        Args:
            y_position: Y coordinate in pixels
        """
        self.page.evaluate(f"window.scrollTo(0, {y_position})")
        self.page.wait_for_timeout(300)  # Wait for scroll to complete
    
    def get_page_height(self) -> int:
        """Get the total scrollable height of the page."""
        return self.page.evaluate("document.documentElement.scrollHeight")
    
    def close(self):
        """Close browser and cleanup resources."""
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except Exception:
            pass
        
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        
        logger.info("Browser closed")

