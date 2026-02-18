"""Metrics utilities for evaluating LLM outputs."""

import json
import re

from patterns.bedrock import call_bedrock


def count_chars(text: str) -> int:
    """Count characters excluding whitespace."""
    return len(text.replace(" ", "").replace("\n", ""))


def avg_sentence_len(text: str) -> float:
    """Average sentence length in word count."""
    sentences = [s.strip() for s in re.split(r'[.!?]\s*', text) if s.strip()]
    if not sentences:
        return 0
    return round(sum(len(s.split()) for s in sentences) / len(sentences), 1)


def evaluate_preservation(original: str, transformed: str) -> dict:
    """Evaluate semantic preservation between original and transformed text using LLM."""
    prompt = f"""Evaluate semantic preservation between original and transformed text.

## Original
{original}

## Transformed
{transformed}

## Criteria
- preservation (1-5): Are all key facts from the original preserved?
- no_distortion (1-5): Is the original meaning undistorted? (5=no distortion)
- tone_shift (1-5): Is the tone/style clearly transformed?

Output JSON only: {{"preservation": N, "no_distortion": N, "tone_shift": N}}"""

    result = call_bedrock(
        "You are a text quality evaluator. Output JSON only.",
        prompt,
        max_tokens=200,
        temperature=0.2,
    )
    try:
        match = re.search(r'\{[^}]+\}', result)
        return json.loads(match.group()) if match else {}
    except (json.JSONDecodeError, AttributeError):
        return {}


def parse_critique_scores(critique_text: str) -> dict:
    """Extract scores from Self-Critique JSON."""
    # Strip markdown code block if present
    text = critique_text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```\s*$', '', text)

    # Try parsing the outermost JSON object
    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            data = json.loads(match.group())
            scores = {k: v.get("score", 0) for k, v in data.items() if isinstance(v, dict) and "score" in v}
            if scores:
                return scores
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: extract individual "key": {"score": N} patterns
    scores = {}
    for m in re.finditer(r'"([^"]+)"\s*:\s*\{\s*"score"\s*:\s*(\d+)', text):
        scores[m.group(1)] = int(m.group(2))
    return scores
