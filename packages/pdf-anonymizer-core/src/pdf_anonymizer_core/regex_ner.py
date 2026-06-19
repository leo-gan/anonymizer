"""Fast first-stage Named Entity Recognition using regular expressions.

The hybrid pipeline (core.anonymize_file) always runs regex NER before
the (more expensive) LLM stage. Matches from regex are later merged
with LLM results using a simple priority system.

This module is intentionally small and dependency-free (beyond stdlib).
You can supply a completely custom `regex_patterns` dict when calling
anonymize_file directly.
"""

import logging
import re
from typing import Dict, List, TypedDict


class EntityDict(TypedDict):
    text: str
    type: str
    base_form: str

def extract_entities_via_regex(text: str, patterns: Dict[str, str]) -> List[EntityDict]:
    """
    Scans the text for PII using pre-configured regular expressions.
    
    Args:
        text: Input text to analyze.
        patterns: Dictionary mapping entity type strings to regex patterns.
        
    Returns:
        A list of EntityDict representing identified PII.
    """
    entities: List[EntityDict] = []
    
    for entity_type, pattern_str in patterns.items():
        try:
            compiled_pattern = re.compile(pattern_str)
            for match in compiled_pattern.finditer(text):
                matched_text = match.group(0)
                # Filter out empty or whitespace-only matches
                if not matched_text.strip():
                    continue
                
                entities.append({
                    "text": matched_text,
                    "type": entity_type.upper(),
                    "base_form": matched_text,
                })
        except re.error as e:
            logging.error(f"Invalid regex pattern configured for {entity_type}: {e}")
            
    return entities
