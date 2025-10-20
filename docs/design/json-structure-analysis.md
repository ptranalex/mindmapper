# Roadmap.sh JSON Structure Analysis

## Data Source

- **Main JSON**: `engineering-manager.json` (~192KB)
  - Contains node graph structure (positions, labels, IDs)
- **Content Files**: `content/` directory (134 markdown files)
  - Contains descriptions and resources for each topic

## JSON Structure

### Top Level

```json
{
  "nodes": [...],  // 228 nodes
  "edges": [...]   // 27 edges (connections between nodes)
}
```

### Node Types

- `section` (25) - Visual containers/groupings
- `subtopic` (133) - Main content nodes (our primary data source)
- `topic` (1) - Similar to subtopic
- `title`, `label`, `paragraph`, `button`, `vertical`, `horizontal`, `linksgroup` - UI elements

### Key Node Structure

```json
{
  "id": "FtWNnOE3zObmjS-Og26M3",
  "type": "subtopic",
  "position": { "x": 123, "y": 456 },
  "data": {
    "label": "Architectural Decision-Making",
    "oldId": "zpphxuz1vaPjnizUm2Qu-" // Optional, used in some nodes
  }
}
```

### Content File Naming

Pattern: `{topic-slug}@{node-id}.md`
Example: `architectural-decision-making@FtWNnOE3zObmjS-Og26M3.md`

The `node-id` matches the node's `id` field in JSON.

### Hierarchy Strategy

1. Use `section` nodes as categories (based on spatial containment)
2. Use `subtopic`/`topic` nodes as actual topics
3. Determine parent-child via:
   - Spatial analysis (x, y positions)
   - OR edges array (if connections are meaningful)
4. Match content files using node ID

## Parsing Strategy

### Step 1: Extract Nodes

- Filter nodes by type: `topic`, `subtopic`
- Build lookup: `node_id -> {label, position}`

### Step 2: Build Hierarchy

- Option A: Use spatial analysis (group by proximity)
- Option B: Use section nodes as containers
- Option C: Simply list all topics (flat structure)

For MVP: **Option C** (flat structure) is simplest and fastest.

### Step 3: Fetch Content

For each topic node:

1. Generate content filename from label (slugify) + node ID
2. Download from GitHub: `content/{filename}.md`
3. Parse markdown for description
4. Extract links as resources

### Step 4: Map to CSV Schema

```
Category, Subcategory, Topic, Description, Resources
```

For flat structure MVP:

- Category: "Engineering Management" (hardcoded)
- Subcategory: "" (empty for now)
- Topic: node label
- Description: from content file
- Resources: URLs extracted from content markdown

## Implementation Notes

- Total topics to process: ~134 (subtopics + topics)
- Each requires 1 HTTP request for content
- Can batch/parallelize for performance
- Cache content files locally for development
