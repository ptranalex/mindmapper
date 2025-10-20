"""JSON parser for roadmap data."""

import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Represents a roadmap node with spatial information."""
    id: str
    label: str
    type: str
    x: float
    y: float
    width: float
    height: float


class RoadmapParser:
    """Parses roadmap JSON and content files."""
    
    def __init__(self, roadmap_name: str = "engineering-manager") -> None:
        """Initialize parser.
        
        Args:
            roadmap_name: Name of the roadmap (used as default category)
        """
        self.roadmap_name = roadmap_name
        self.category = self._format_category_name(roadmap_name)
    
    def extract_topics(self, roadmap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract topic nodes from roadmap JSON with graph-based hierarchy detection.
        
        Args:
            roadmap_data: Parsed roadmap JSON
        
        Returns:
            List of topic dictionaries with id, label, position, category, subcategory
        """
        nodes = roadmap_data.get('nodes', [])
        edges = roadmap_data.get('edges', [])
        
        # Extract all nodes with spatial information
        all_nodes = self._extract_all_nodes(nodes)
        
        # Build graph structures for hierarchy detection
        parent_map = self._build_parent_graph(edges)
        nodes_by_id = {n.id: n for n in all_nodes}
        
        # Get leaf nodes (topics/subtopics we want to extract)
        topic_nodes = [n for n in all_nodes if n.type in ['topic', 'subtopic']]
        
        logger.info(f"Found {len(topic_nodes)} topic nodes with {len(edges)} edges")
        
        # Detect hierarchy for each topic using graph traversal
        topics = []
        for topic_node in topic_nodes:
            category, subcategory = self._detect_hierarchy(
                topic_node, 
                parent_map, 
                nodes_by_id
            )
            
            topic_data = {
                'id': topic_node.id,
                'label': topic_node.label,
                'type': topic_node.type,
                'position': {'x': topic_node.x, 'y': topic_node.y},
                'category': category,
                'subcategory': subcategory,
            }
            topics.append(topic_data)
        
        # Log hierarchy detection stats
        with_category = sum(1 for t in topics if t['category'] != self.category)
        with_subcategory = sum(1 for t in topics if t['subcategory'])
        logger.info(f"Hierarchy detection: {with_category}/{len(topics)} have detected category, "
                   f"{with_subcategory}/{len(topics)} have subcategory")
        
        return topics
    
    def _extract_all_nodes(self, nodes: List[Dict[str, Any]]) -> List[Node]:
        """Extract all nodes with spatial information.
        
        Args:
            nodes: Raw node data from JSON
        
        Returns:
            List of Node objects with position and size
        """
        result = []
        for node in nodes:
            node_type = node.get('type', '')
            position = node.get('position', {})
            
            # Skip nodes without position data
            if not position or 'x' not in position or 'y' not in position:
                continue
            
            # Get dimensions
            width = node.get('width', 0)
            height = node.get('height', 0)
            
            # Get label
            label = node.get('data', {}).get('label', '')
            if not label:
                continue
            
            node_obj = Node(
                id=node.get('id', ''),
                label=label,
                type=node_type,
                x=float(position['x']),
                y=float(position['y']),
                width=float(width),
                height=float(height)
            )
            result.append(node_obj)
        
        return result
    
    def _build_parent_graph(self, edges: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build parent lookup from edge data.
        
        Args:
            edges: Edge data from roadmap JSON
        
        Returns:
            Dict mapping child_id -> parent_id
        """
        parent_of = {}
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target:
                parent_of[target] = source
        return parent_of
    
    def _find_ancestor_chain(
        self, 
        node_id: str, 
        parent_map: Dict[str, str], 
        nodes_by_id: Dict[str, Node], 
        max_depth: int = 10
    ) -> List[Node]:
        """Find all ancestors of a node up the parent chain.
        
        Args:
            node_id: Starting node ID
            parent_map: Dict of child_id -> parent_id
            nodes_by_id: Dict of node_id -> Node object
            max_depth: Maximum ancestor levels to traverse
        
        Returns:
            List of ancestor Nodes from immediate parent to root
        """
        ancestors = []
        current_id = node_id
        
        for _ in range(max_depth):
            parent_id = parent_map.get(current_id)
            if not parent_id:
                break
            
            parent_node = nodes_by_id.get(parent_id)
            if parent_node and parent_node.label:  # Only include labeled nodes
                ancestors.append(parent_node)
            
            current_id = parent_id
        
        return ancestors
    
    def _infer_from_siblings(
        self, 
        node: Node, 
        parent_map: Dict[str, str], 
        nodes_by_id: Dict[str, Node]
    ) -> str:
        """Infer category by finding siblings with same parent.
        
        If siblings have a common category, use that.
        Otherwise, use node's own label or roadmap default.
        
        Args:
            node: Node to infer category for
            parent_map: Dict of child_id -> parent_id
            nodes_by_id: Dict of node_id -> Node object
        
        Returns:
            Inferred category name
        """
        # Find this node's parent (might be None)
        parent_id = parent_map.get(node.id)
        
        if parent_id:
            parent_node = nodes_by_id.get(parent_id)
            if parent_node and parent_node.label:
                return parent_node.label
        
        # No parent or parent has no label: use node's own label
        return node.label if node.label else self.category
    
    def _find_nearest_parent(self, child: Node, potential_parents: List[Node]) -> Optional[Node]:
        """Find the nearest parent label above the child node.
        
        Roadmaps use labels as section headers positioned ABOVE their topics,
        not as containers. We find the closest label that's above and within
        a reasonable horizontal distance.
        
        Args:
            child: Child node (topic/subtopic)
            potential_parents: List of potential parent nodes (labels)
        
        Returns:
            Nearest parent node, or None if no suitable parent found
        """
        if not potential_parents:
            return None
        
        # Find labels that are above this topic (smaller y value)
        # and within reasonable horizontal range (±500px)
        candidates = []
        for parent in potential_parents:
            # Check if label is above the topic
            if parent.y < child.y:
                # Check horizontal proximity (labels should be somewhat aligned)
                horizontal_distance = abs(parent.x - child.x)
                if horizontal_distance < 800:  # Reasonable horizontal threshold
                    vertical_distance = child.y - parent.y
                    # Prefer closer labels
                    candidates.append((vertical_distance + horizontal_distance * 0.5, parent))
        
        if not candidates:
            return None
        
        # Return the closest label (by combined distance)
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    
    def _detect_hierarchy(
        self, 
        topic_node: Node, 
        parent_map: Dict[str, str], 
        nodes_by_id: Dict[str, Node]
    ) -> Tuple[str, str]:
        """Detect category and subcategory using graph traversal.
        
        Strategy:
        1. Find ancestor chain from leaf up to root
        2. Filter to only labeled ancestors (label, topic, paragraph types)
        3. Assign:
           - Category: furthest meaningful ancestor (root level)
           - Subcategory: intermediate ancestor if exists
        
        Fallback for nodes with no ancestors:
        - Try to infer from sibling nodes at same level
        - Otherwise use roadmap name as category
        
        Args:
            topic_node: Topic/subtopic node to classify
            parent_map: Dict of child_id -> parent_id
            nodes_by_id: Dict of node_id -> Node object
        
        Returns:
            Tuple of (category, subcategory)
        """
        ancestors = self._find_ancestor_chain(
            topic_node.id, 
            parent_map, 
            nodes_by_id
        )
        
        if not ancestors:
            # No parents: check siblings for inference
            category = self._infer_from_siblings(topic_node, parent_map, nodes_by_id)
            return category, ""
        
        # Filter to meaningful ancestors (with labels, not layout nodes)
        meaningful = [a for a in ancestors if a.type in ['label', 'topic', 'paragraph']]
        
        if len(meaningful) == 0:
            return self.category, ""
        elif len(meaningful) == 1:
            # 2-level: Category only
            return meaningful[0].label, ""
        else:
            # 3-level: Category (furthest) → Subcategory (closest)
            return meaningful[-1].label, meaningful[0].label
    
    def parse_content(self, content: str) -> Dict[str, str]:
        """Parse markdown content to extract description and resources.
        
        Args:
            content: Markdown content string
        
        Returns:
            Dict with 'description' and 'resources' keys
        """
        if not content:
            return {'description': '', 'resources': ''}
        
        # Extract description (all text before resources section)
        description = self._extract_description(content)
        
        # Extract resource URLs
        resources = self._extract_resources(content)
        
        return {
            'description': description,
            'resources': resources
        }
    
    def _extract_description(self, content: str) -> str:
        """Extract description text from markdown.
        
        Args:
            content: Markdown content
        
        Returns:
            Description text
        """
        # Remove markdown headings (lines starting with #)
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            # Skip heading lines and empty lines
            if stripped and not stripped.startswith('#'):
                # Remove markdown links but keep text: [text](url) -> text
                line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
                lines.append(stripped)
        
        # Join paragraphs with space
        description = ' '.join(lines)
        return description.strip()
    
    def _extract_resources(self, content: str) -> str:
        """Extract URLs from markdown content.
        
        Args:
            content: Markdown content
        
        Returns:
            Pipe-separated URLs
        """
        # Find all markdown links: [text](url)
        url_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        matches = re.findall(url_pattern, content)
        
        # Extract URLs (second group in match)
        urls = [url for (text, url) in matches if url.startswith('http')]
        
        # Also find bare URLs
        bare_url_pattern = r'https?://[^\s\)]+'
        bare_urls = re.findall(bare_url_pattern, content)
        
        # Combine and deduplicate
        all_urls = list(dict.fromkeys(urls + bare_urls))
        
        return '|'.join(all_urls)
    
    def _format_category_name(self, name: str) -> str:
        """Format roadmap name as category.
        
        Args:
            name: Roadmap name (e.g., 'engineering-manager')
        
        Returns:
            Formatted name (e.g., 'Engineering Manager')
        """
        # Replace hyphens with spaces and title case
        return name.replace('-', ' ').title()

