"""Prompt templates for enrichment."""

import json
from typing import Dict, Any, List

SYSTEM_PROMPT = """You are an expert educator evaluating technical learning topics."""

RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "tldr": {
            "type": "string",
            "description": "≤12 words, crisp summary, no punctuation at end",
        },
        "challenge": {
            "type": "string",
            "enum": ["practice", "expert"],
            "description": "practice: fundamental skills, shallow breadth; expert: advanced/architecture, heavy prereqs",
        },
    },
    "required": ["tldr", "challenge"],
}

BATCH_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "tldr": {
                "type": "string",
                "description": "≤12 words, crisp summary, no punctuation at end",
            },
            "challenge": {
                "type": "string",
                "enum": ["practice", "expert"],
                "description": "practice: fundamental skills, shallow breadth; expert: advanced/architecture, heavy prereqs",
            },
        },
        "required": ["id", "tldr", "challenge"],
    },
}


def build_prompt(category: str, subcategory: str, topic: str, description: str) -> str:
    """Build enrichment prompt from row data.

    Args:
        category: Category name
        subcategory: Subcategory name
        topic: Topic name
        description: Description text

    Returns:
        Formatted prompt string
    """
    # Truncate description if too long to stay within token limits
    desc = description[:500] if description else "N/A"

    return f"""System: {SYSTEM_PROMPT}

Context:
- Category: {category or 'N/A'}
- Subcategory: {subcategory or 'N/A'}
- Topic: {topic}
- Description: {desc}

Task:
1. Generate a TLDR (≤12 words, no ending punctuation)
2. Classify challenge level:
   - "practice": fundamental skills, shallow breadth, few prerequisites
   - "expert": advanced/architecture/production, heavy prerequisites, deep trade-offs

Output JSON with "tldr" and "challenge" fields."""


def build_batch_prompt(rows: List[Dict[str, str]]) -> str:
    """Build batch enrichment prompt.

    Args:
        rows: List of row dictionaries with Category, Subcategory, Topic, Description

    Returns:
        Formatted batch prompt string
    """
    topics = []
    for i, row in enumerate(rows):
        topics.append(
            {
                "id": str(i),
                "category": row.get("Category", ""),
                "subcategory": row.get("Subcategory", ""),
                "topic": row["Topic"],
                "description": (row.get("Description", "")[:500]),  # Truncate
            }
        )

    prompt = f"""System: You are an expert educator evaluating technical learning topics.

Evaluate the following {len(topics)} topics in batch.

For each topic, provide:
1. TLDR (≤12 words, no ending punctuation)
2. Challenge level:
   - "practice": fundamental skills, shallow breadth, few prerequisites
   - "expert": advanced/architecture/production, heavy prerequisites, deep trade-offs

Topics to evaluate:
{json.dumps(topics, indent=2)}

Output a JSON array with "id", "tldr", and "challenge" for each topic."""

    return prompt
