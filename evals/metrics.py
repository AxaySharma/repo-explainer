"""Metrics module for scoring agent answers.

Contains functions to measure topic coverage, evaluate hallucination penalties,
check answer length constraints, score groundedness, compute the overall weighted score,
and locate missing topics.
"""

from typing import List

def score_topic_coverage(answer: str, expected_topics: List[str]) -> float:
    """Calculate the fraction of expected topics that appear in the answer (case-insensitive)."""
    if not expected_topics:
        return 1.0
    
    answer_lower = answer.lower()
    found_count = 0
    for topic in expected_topics:
        if topic.lower() in answer_lower:
            found_count += 1
            
    return found_count / len(expected_topics)

def score_hallucination_penalty(answer: str, must_not_contain: List[str]) -> float:
    """Return 0.0 if any forbidden word appears in the answer (case-insensitive), otherwise 1.0."""
    if not must_not_contain:
        return 1.0
        
    answer_lower = answer.lower()
    for forbidden in must_not_contain:
        if forbidden.lower() in answer_lower:
            return 0.0
            
    return 1.0

def score_answer_length(answer: str, min_words: int = 50, max_words: int = 800) -> float:
    """Evaluate if the answer's word count satisfies constraints, penalizing short/long responses."""
    words = answer.split()
    word_count = len(words)
    
    if min_words <= word_count <= max_words:
        return 1.0
    elif word_count < min_words:
        if min_words == 0:
            return 1.0
        return word_count / min_words
    else:
        if word_count == 0:
            return 0.0
        return max_words / word_count

def score_groundedness(answer: str, tools_used: List[str]) -> float:
    """Score the groundedness of the response based on exploration tools executed by the agent."""
    if not tools_used:
        return 0.0
        
    # High-value reading/exploring tools
    if "read_file" in tools_used or "search_code" in tools_used:
        return 1.0
        
    # Structural inspection tools only
    if "get_file_tree" in tools_used or "list_directory" in tools_used:
        return 0.7
        
    return 0.5

def compute_overall_score(
    topic: float,
    hallucination: float,
    length: float,
    groundedness: float
) -> float:
    """Compute the weighted average of the four metrics, rounded to 4 decimal places."""
    weighted_sum = (topic * 0.40) + (hallucination * 0.30) + (length * 0.15) + (groundedness * 0.15)
    return round(weighted_sum, 4)

def get_missing_topics(answer: str, expected_topics: List[str]) -> List[str]:
    """Retrieve all expected topics that did not appear in the answer (case-insensitive)."""
    if not expected_topics:
        return []
        
    answer_lower = answer.lower()
    missing = []
    for topic in expected_topics:
        if topic.lower() not in answer_lower:
            missing.append(topic)
            
    return missing
