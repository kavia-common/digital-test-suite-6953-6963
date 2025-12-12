"""
Domain models and in-memory repositories for the backend.

This package provides:
- Data models (User, Test, Submission)
- In-memory repositories that support CRUD and basic analytics
"""

from .models import User, Test, Submission, create_uuid
from .repositories import (
    InMemoryUserRepository,
    InMemoryTestRepository,
    InMemorySubmissionRepository,
    InMemoryUnitOfWork,
)

__all__ = [
    "User",
    "Test",
    "Submission",
    "create_uuid",
    "InMemoryUserRepository",
    "InMemoryTestRepository",
    "InMemorySubmissionRepository",
    "InMemoryUnitOfWork",
]
