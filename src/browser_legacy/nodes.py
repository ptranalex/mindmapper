"""Node extraction and hierarchy inference for roadmap structure."""

import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional
from playwright.sync_api import Page, Locator, ElementHandle

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box coordinates."""
    x: float
    y: float
    width: float
    height: float
    
    def contains(self, other: 'BoundingBox', tolerance: float = 3.0) -> bool:
        """Check if this box contains another box with tolerance.
        
        Args:
            other: The box to check
            tolerance: Pixel tolerance for containment check
        
        Returns:
            True if this box contains the other box
        """
        return (
            self.x - tolerance <= other.x and
            self.y - tolerance <= other.y and
            self.x + self.width + tolerance >= other.x + other.width and
            self.y + self.height + tolerance >= other.y + other.height
        )
    
    def overlaps_x(self, other: 'BoundingBox') -> bool:
        """Check if this box overlaps horizontally with another box."""
        return not (self.x + self.width < other.x or other.x + other.width < self.x)


@dataclass
class RoadmapNode:
    """Represents a node in the roadmap."""
    text: str
    bbox: BoundingBox
    element: ElementHandle
    node_type: str  # 'container' or 'leaf'
    category: str = ""
    subcategory: str = ""
    
    def __hash__(self):
        """Hash based on text and position for deduplication."""
        return hash((self.text, round(self.bbox.x), round(self.bbox.y), 
                    round(self.bbox.width), round(self.bbox.height)))
    
    def __eq__(self, other):
        """Equality based on hash."""
        if not isinstance(other, RoadmapNode):
            return False
        return hash(self) == hash(other)


class NodeExtractor:
    """Extracts and classifies nodes from the roadmap page."""
    
    # Selector fallback chain
    NODE_SELECTORS = [
        'svg g:has(rect):has(text)',  # SVG-based nodes
        '[data-node-id]',  # Data attribute nodes
        '[data-type="topic"]',
        '.clickable-node',
        'button[data-node]',
    ]
    
    # Size thresholds for classification
    CONTAINER_WIDTH_THRESHOLD = 300
    CONTAINER_HEIGHT_THRESHOLD = 150
    
    def __init__(self, page: Page):
        """Initialize node extractor.
        
        Args:
            page: Playwright page object
        """
        self.page = page
    
    def extract_all_nodes(self) -> List[RoadmapNode]:
        """Extract all nodes from the page with scroll sweep.
        
        Returns:
            List of unique RoadmapNode objects
        """
        logger.info("Starting node extraction with scroll sweep")
        
        nodes_set = set()
        viewport_height = self.page.viewport_size['height']
        page_height = self.page.evaluate("document.documentElement.scrollHeight")
        
        # Calculate scroll positions (100vh increments)
        scroll_positions = list(range(0, page_height, viewport_height))
        if scroll_positions[-1] < page_height:
            scroll_positions.append(page_height)
        
        logger.info(f"Will scroll to {len(scroll_positions)} positions (page height: {page_height}px)")
        
        for i, y_pos in enumerate(scroll_positions):
            self.page.evaluate(f"window.scrollTo(0, {y_pos})")
            self.page.wait_for_timeout(500)  # Wait for content to render
            
            nodes_at_position = self._extract_visible_nodes()
            nodes_set.update(nodes_at_position)
            logger.debug(f"Scroll position {i+1}/{len(scroll_positions)}: found {len(nodes_at_position)} nodes "
                        f"(total unique: {len(nodes_set)})")
        
        # Convert to list and sort by position (top to bottom, left to right)
        nodes_list = sorted(nodes_set, key=lambda n: (n.bbox.y, n.bbox.x))
        
        logger.info(f"Extracted {len(nodes_list)} unique nodes after deduplication")
        return nodes_list
    
    def _extract_visible_nodes(self) -> List[RoadmapNode]:
        """Extract nodes visible in current viewport.
        
        Returns:
            List of RoadmapNode objects found in viewport
        """
        nodes = []
        
        # Try each selector in the fallback chain
        for selector in self.NODE_SELECTORS:
            try:
                elements = self.page.locator(selector).element_handles()
                
                for element in elements:
                    try:
                        # Get bounding box
                        bbox_dict = element.bounding_box()
                        if not bbox_dict:
                            continue
                        
                        bbox = BoundingBox(**bbox_dict)
                        
                        # Get text content
                        text = element.text_content() or ""
                        text = text.strip()
                        if not text:
                            continue
                        
                        # Classify node type based on size
                        node_type = self._classify_node_type(bbox)
                        
                        node = RoadmapNode(
                            text=text,
                            bbox=bbox,
                            element=element,
                            node_type=node_type
                        )
                        nodes.append(node)
                    
                    except Exception as e:
                        logger.debug(f"Error extracting individual node: {e}")
                        continue
                
                if nodes:
                    logger.debug(f"Found {len(nodes)} nodes with selector: {selector}")
                    break  # Found nodes, stop trying selectors
            
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        return nodes
    
    def _classify_node_type(self, bbox: BoundingBox) -> str:
        """Classify node as container or leaf based on size.
        
        Args:
            bbox: Bounding box of the node
        
        Returns:
            'container' or 'leaf'
        """
        if (bbox.width > self.CONTAINER_WIDTH_THRESHOLD or 
            bbox.height > self.CONTAINER_HEIGHT_THRESHOLD):
            return 'container'
        return 'leaf'
    
    def infer_hierarchy(self, nodes: List[RoadmapNode]) -> List[RoadmapNode]:
        """Infer hierarchical relationships based on geometry.
        
        Args:
            nodes: List of extracted nodes
        
        Returns:
            Same list with category/subcategory fields populated
        """
        logger.info("Inferring hierarchy from node geometry")
        
        containers = [n for n in nodes if n.node_type == 'container']
        leaves = [n for n in nodes if n.node_type == 'leaf']
        
        logger.info(f"Found {len(containers)} containers and {len(leaves)} leaf nodes")
        
        # First, establish container hierarchy (subcategories within categories)
        container_parents = {}
        for container in containers:
            # Find smallest container that encloses this one
            potential_parents = [
                c for c in containers 
                if c != container and c.bbox.contains(container.bbox)
            ]
            if potential_parents:
                # Sort by area (smallest first)
                potential_parents.sort(key=lambda c: c.bbox.width * c.bbox.height)
                container_parents[container] = potential_parents[0]
        
        # Assign categories and subcategories to containers
        for container in containers:
            if container in container_parents:
                # This is a subcategory
                parent = container_parents[container]
                container.category = parent.text
                container.subcategory = container.text
            else:
                # This is a top-level category
                container.category = container.text
                container.subcategory = ""
        
        # Assign leaf nodes to their containers
        for leaf in leaves:
            enclosing_containers = [
                c for c in containers 
                if c.bbox.contains(leaf.bbox)
            ]
            
            if enclosing_containers:
                # Assign to smallest enclosing container
                enclosing_containers.sort(key=lambda c: c.bbox.width * c.bbox.height)
                smallest_container = enclosing_containers[0]
                leaf.category = smallest_container.category
                leaf.subcategory = smallest_container.subcategory
            else:
                # Fallback: find nearest container above with overlapping x-range
                leaf.category, leaf.subcategory = self._find_nearest_header(leaf, containers)
        
        assigned_count = sum(1 for n in leaves if n.category)
        logger.info(f"Assigned hierarchy to {assigned_count}/{len(leaves)} leaf nodes")
        
        return nodes
    
    def _find_nearest_header(self, leaf: RoadmapNode, containers: List[RoadmapNode]) -> Tuple[str, str]:
        """Find nearest container above with overlapping x-range.
        
        Args:
            leaf: The leaf node to find a header for
            containers: List of container nodes
        
        Returns:
            Tuple of (category, subcategory)
        """
        # Filter to containers above the leaf
        candidates = [
            c for c in containers 
            if c.bbox.y < leaf.bbox.y and c.bbox.overlaps_x(leaf.bbox)
        ]
        
        if not candidates:
            return ("Uncategorized", "")
        
        # Sort by distance (closest first)
        candidates.sort(key=lambda c: leaf.bbox.y - (c.bbox.y + c.bbox.height))
        nearest = candidates[0]
        
        return (nearest.category, nearest.subcategory)

