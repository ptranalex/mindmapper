"""Prompt templates for enrichment."""

from typing import Dict, Any

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
