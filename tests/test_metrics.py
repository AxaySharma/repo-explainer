"""
Unit tests for evals/metrics.py
These run in CI without needing an Anthropic API key.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.metrics import (
    score_topic_coverage,
    score_hallucination_penalty,
    score_answer_length,
    score_groundedness,
    compute_overall_score,
    get_missing_topics,
)


# --- score_topic_coverage ---

def test_topic_coverage_all_found():
    answer = "This project uses FastAPI and SQLite with JWT auth"
    topics = ["fastapi", "sqlite", "jwt"]
    assert score_topic_coverage(answer, topics) == 1.0


def test_topic_coverage_none_found():
    answer = "This project uses Django and PostgreSQL"
    topics = ["fastapi", "sqlite", "jwt"]
    assert score_topic_coverage(answer, topics) == 0.0


def test_topic_coverage_partial():
    answer = "This project uses FastAPI"
    topics = ["fastapi", "sqlite", "jwt"]
    score = score_topic_coverage(answer, topics)
    assert round(score, 4) == round(1/3, 4)


def test_topic_coverage_empty_topics():
    assert score_topic_coverage("anything", []) == 1.0


def test_topic_coverage_case_insensitive():
    answer = "Built with FASTAPI and SQLITE"
    topics = ["fastapi", "sqlite"]
    assert score_topic_coverage(answer, topics) == 1.0


# --- score_hallucination_penalty ---

def test_hallucination_penalty_clean():
    answer = "This uses FastAPI and SQLite"
    must_not = ["django", "postgresql"]
    assert score_hallucination_penalty(answer, must_not) == 1.0


def test_hallucination_penalty_hit():
    answer = "This uses Django and PostgreSQL"
    must_not = ["django", "postgresql"]
    assert score_hallucination_penalty(answer, must_not) == 0.0


def test_hallucination_penalty_empty():
    assert score_hallucination_penalty("anything", []) == 1.0


def test_hallucination_penalty_case_insensitive():
    answer = "This uses DJANGO framework"
    must_not = ["django"]
    assert score_hallucination_penalty(answer, must_not) == 0.0


# --- score_answer_length ---

def test_length_in_range():
    answer = " ".join(["word"] * 100)
    assert score_answer_length(answer, min_words=50, max_words=800) == 1.0


def test_length_too_short():
    answer = " ".join(["word"] * 25)
    score = score_answer_length(answer, min_words=50, max_words=800)
    assert score == 25 / 50


def test_length_too_long():
    answer = " ".join(["word"] * 1000)
    score = score_answer_length(answer, min_words=50, max_words=800)
    assert score == 800 / 1000


def test_length_exactly_at_min():
    answer = " ".join(["word"] * 50)
    assert score_answer_length(answer, min_words=50, max_words=800) == 1.0


def test_length_exactly_at_max():
    answer = " ".join(["word"] * 800)
    assert score_answer_length(answer, min_words=50, max_words=800) == 1.0


# --- score_groundedness ---

def test_groundedness_read_file():
    assert score_groundedness("answer", ["read_file", "get_file_tree"]) == 1.0


def test_groundedness_search_code():
    assert score_groundedness("answer", ["search_code"]) == 1.0


def test_groundedness_tree_only():
    assert score_groundedness("answer", ["get_file_tree"]) == 0.7


def test_groundedness_empty_tools():
    assert score_groundedness("answer", []) == 0.0


def test_groundedness_other_tools():
    assert score_groundedness("answer", ["list_directory"]) == 0.7


# --- compute_overall_score ---

def test_overall_score_perfect():
    score = compute_overall_score(1.0, 1.0, 1.0, 1.0)
    assert score == 1.0


def test_overall_score_zero():
    score = compute_overall_score(0.0, 0.0, 0.0, 0.0)
    assert score == 0.0


def test_overall_score_weights():
    # topic=1.0 (40%), hallucination=0.0 (30%), length=1.0 (15%), groundedness=1.0 (15%)
    # Expected: 0.4 + 0.0 + 0.15 + 0.15 = 0.70
    score = compute_overall_score(1.0, 0.0, 1.0, 1.0)
    assert score == round(0.70, 4)


# --- get_missing_topics ---

def test_missing_topics_none_missing():
    answer = "fastapi sqlite jwt auth"
    topics = ["fastapi", "sqlite", "jwt"]
    assert get_missing_topics(answer, topics) == []


def test_missing_topics_all_missing():
    answer = "django postgresql"
    topics = ["fastapi", "sqlite", "jwt"]
    assert set(get_missing_topics(answer, topics)) == {"fastapi", "sqlite", "jwt"}


def test_missing_topics_partial():
    answer = "fastapi is great"
    topics = ["fastapi", "sqlite", "jwt"]
    missing = get_missing_topics(answer, topics)
    assert "fastapi" not in missing
    assert "sqlite" in missing
    assert "jwt" in missing