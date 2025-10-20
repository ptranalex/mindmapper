"""Prompt templates for enrichment."""

import json
from typing import Dict, Any, List

SYSTEM_PROMPT = """You are an expert educator evaluating technical learning topics."""

RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "tldr": {
            "type": "string",
            "description": "≤12 words; what it is + why it matters; plain language; no trailing punctuation",
            "maxLength": 120,
            "pattern": r"^(?!.*[.!?]\s*$).{1,120}$",
        },
        "challenge": {
            "type": "string",
            "description": "≤12 words; state the core obstacle + its context/constraint; plain language; no trailing punctuation",
            "maxLength": 120,
            "pattern": r"^(?!.*[.!?]\s*$).{1,120}$",
        },
        "how_to": {
            "type": "string",
            "description": "Multi-line formatted learning guide with Steps (3-7 items), optional Guardrails and Signals of Done",
            "maxLength": 800,
        },
    },
    "required": ["tldr", "challenge", "how_to"],
}

BATCH_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "tldr": {
                "type": "string",
                "description": "≤12 words; what it is + why it matters; plain language; no trailing punctuation",
                "maxLength": 120,
                "pattern": r"^(?!.*[.!?]\s*$).{1,120}$",
            },
            "challenge": {
                "type": "string",
                "description": "≤12 words; state the core obstacle + its context/constraint; plain language; no trailing punctuation",
                "maxLength": 120,
                "pattern": r"^(?!.*[.!?]\s*$).{1,120}$",
            },
            "how_to": {
                "type": "string",
                "description": "Multi-line formatted learning guide with Steps (3-7 items), optional Guardrails and Signals of Done",
                "maxLength": 800,
            },
        },
        "required": ["id", "tldr", "challenge", "how_to"],
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
2. Generate a Challenge (≤12 words, state the core obstacle + context)
3. Generate a How-To (multi-line learning guide, format exactly as shown):

   Format:
   Steps:
   - [action step 1, ≤9 words, imperative, no punctuation]
   - [action step 2, ≤9 words, imperative, no punctuation]
   - [3-7 total steps]
   Guardrails:
   - [common pitfall to avoid]
   Signals of Done:
   - [how to know you've mastered it]
   
   Guidelines:
   - Use PACE framework (Practice, Apply, Critique, Extend)
   - Steps: 3-7 action items, imperative voice, ≤9 words each
   - Guardrails: Common mistakes to avoid (optional, max 5)
   - Signals of Done: Mastery indicators (optional, max 5)

Output JSON with "tldr", "challenge", and "how_to" fields."""


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
1. TLDR (≤12 words; what it is + why it matters; plain language; no trailing punctuation)
2. Challenge (≤12 words; state the core obstacle + its context/constraint; plain language; no trailing punctuation)
3. How-To (multi-line formatted string with  Steps (3-7), optional Guardrails/Signals)
   - Format: "Steps:\\n- step1\\n- step2\\n..."
   - Each step ≤9 words, imperative, no punctuation
   - PACE framework: Practice, Apply, Critique, Extend
   - Optional: Guardrails (pitfalls) and Signals of Done (mastery indicators)

Topics to evaluate:
{json.dumps(topics, indent=2)}

Output a JSON array with "id", "tldr", "challenge", and "how_to" for each topic."""

    return prompt
