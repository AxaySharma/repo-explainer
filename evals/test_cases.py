"""Test cases for evaluating the Repo Explainer Agent.

Defines the TestCase dataclass and the 8 core evaluation scenarios covering different
aspects of the sample user management codebase.
"""

import dataclasses
from typing import List

@dataclasses.dataclass
class TestCase:
    """Represents a single evaluation test case for the agent."""
    id: str
    question: str
    expected_topics: List[str]
    must_not_contain: List[str]
    description: str
    min_words: int = 50
    max_words: int = 800

TEST_CASES: List[TestCase] = [
    TestCase(
        id="architecture_overview",
        question="What is the overall architecture of this project?",
        expected_topics=["fastapi", "sqlite", "jwt", "auth", "database", "models", "routes", "main"],
        must_not_contain=["django", "postgresql", "mongodb", "flask", "express", "spring"],
        description="Agent should map out all components and how they connect"
    ),
    TestCase(
        id="framework_detection",
        question="What framework and language is this project built with?",
        expected_topics=["fastapi", "python", "pydantic", "uvicorn"],
        must_not_contain=["django", "flask", "javascript", "node", "ruby", "java", "go"],
        description="Agent should correctly identify FastAPI and Python"
    ),
    TestCase(
        id="auth_mechanism",
        question="How does authentication work in this codebase?",
        expected_topics=["jwt", "token", "bearer", "secret", "decode", "require_auth", "authorization", "header"],
        must_not_contain=["oauth", "session", "cookie", "basic auth", "api key", "no authentication"],
        description="Agent should explain JWT auth flow end to end"
    ),
    TestCase(
        id="database_layer",
        question="What database does this project use and how is it accessed?",
        expected_topics=["sqlite", "database.py", "get_db", "connect", "sql", "singleton", "connection"],
        must_not_contain=["postgresql", "mysql", "mongodb", "redis", "orm", "sqlalchemy", "no database"],
        description="Agent should identify SQLite and explain the database.py layer"
    ),
    TestCase(
        id="api_endpoints",
        question="List all the API endpoints and what each one does.",
        expected_topics=["health", "login", "users", "get", "post", "auth", "jwt", "create"],
        must_not_contain=["delete", "put", "patch", "graphql", "websocket", "no endpoints"],
        description="Agent should list all 5 endpoints with methods and purposes"
    ),
    TestCase(
        id="data_models",
        question="What are the main data models in this project?",
        expected_topics=["user", "usercreate", "loginrequest", "tokenresponse", "pydantic", "email", "password"],
        must_not_contain=["sqlalchemy", "django model", "no models", "no schema", "mongodb"],
        description="Agent should describe all Pydantic models from models.py"
    ),
    TestCase(
        id="running_locally",
        question="How would I run this project locally?",
        expected_topics=["uvicorn", "pip install", "requirements", "main:app", "python"],
        must_not_contain=["docker", "kubernetes", "npm", "yarn", "cannot run", "no instructions"],
        description="Agent should give accurate run instructions from README"
    ),
    TestCase(
        id="adding_endpoint",
        question="Which files would I need to modify to add a new API endpoint?",
        expected_topics=["main.py", "models.py", "database.py", "route", "pydantic", "function"],
        must_not_contain=["no files", "any file", "cannot determine", "not possible"],
        description="Agent should identify main.py and potentially models.py/database.py"
    )
]
