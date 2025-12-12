"""
In-memory repositories and a simple Unit of Work abstraction.

These classes are designed to be swapped later for a database-backed implementation
without changing the service/route layer contracts.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Callable, Any, Tuple
from copy import deepcopy

from .models import User, Test, Submission, create_uuid


class InMemoryBaseRepository:
    """
    Generic in-memory repository. Stores items in a dict keyed by id.
    """

    def __init__(self) -> None:
        self._items: Dict[str, Any] = {}

    def _clone(self, item: Any) -> Any:
        # Create a defensive copy to avoid external mutation
        return deepcopy(item)

    def _match(self, item: Any, where: Optional[Callable[[Any], bool]]) -> bool:
        if where is None:
            return True
        try:
            return where(item)
        except Exception:
            return False

    def list(self, where: Optional[Callable[[Any], bool]] = None, limit: Optional[int] = None, offset: int = 0) -> List[Any]:
        """
        List items with optional predicate, pagination via limit/offset.
        """
        items = [self._clone(v) for v in self._items.values() if self._match(v, where)]
        items.sort(key=lambda x: getattr(x, "created_at", ""))
        if offset:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items

    def get(self, item_id: str) -> Optional[Any]:
        """
        Get a single item by id.
        """
        item = self._items.get(item_id)
        return self._clone(item) if item else None

    def create(self, item: Any) -> Any:
        """
        Create a new item. If id missing/empty, assign one.
        """
        if not getattr(item, "id", None):
            item.id = create_uuid()
        # Validate if available
        if hasattr(item, "validate"):
            item.validate()  # type: ignore[attr-defined]
        self._items[item.id] = self._clone(item)
        return self._clone(item)

    def upsert(self, item: Any) -> Any:
        """
        Create or replace an item by id.
        """
        if not getattr(item, "id", None):
            item.id = create_uuid()
        if hasattr(item, "validate"):
            item.validate()  # type: ignore[attr-defined]
        self._items[item.id] = self._clone(item)
        return self._clone(item)

    def update(self, item_id: str, patch: Dict[str, Any]) -> Optional[Any]:
        """
        Update fields on an existing item. Returns updated item or None.
        """
        if item_id not in self._items:
            return None
        obj = self._items[item_id]
        # Apply patch
        for k, v in patch.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        # touch if available
        if hasattr(obj, "touch"):
            obj.touch()  # type: ignore[attr-defined]
        # validate if available
        if hasattr(obj, "validate"):
            obj.validate()  # type: ignore[attr-defined]
        self._items[item_id] = self._clone(obj)
        return self._clone(obj)

    def delete(self, item_id: str) -> bool:
        """
        Delete an item by id. Returns True if existed.
        """
        return self._items.pop(item_id, None) is not None

    def count(self, where: Optional[Callable[[Any], bool]] = None) -> int:
        """
        Count items optionally filtered by predicate.
        """
        return sum(1 for v in self._items.values() if self._match(v, where))


class InMemoryUserRepository(InMemoryBaseRepository):
    """
    In-memory repository for users with convenience getters.
    """

    def find_by_email(self, email: str) -> Optional[User]:
        for user in self._items.values():
            if isinstance(user, User) and user.email.lower() == email.lower():
                return self._clone(user)
        return None

    def list_by_role(self, role: str) -> List[User]:
        return [self._clone(u) for u in self._items.values() if isinstance(u, User) and u.role == role]


class InMemoryTestRepository(InMemoryBaseRepository):
    """
    In-memory repository for tests with convenience queries.
    """

    def list_by_author(self, author_id: str) -> List[Test]:
        return [self._clone(t) for t in self._items.values() if isinstance(t, Test) and t.author_id == author_id]

    def list_published(self) -> List[Test]:
        return [self._clone(t) for t in self._items.values() if isinstance(t, Test) and t.published]


class InMemorySubmissionRepository(InMemoryBaseRepository):
    """
    In-memory repository for submissions with analytics helpers.
    """

    def list_by_user(self, user_id: str) -> List[Submission]:
        return [self._clone(s) for s in self._items.values() if isinstance(s, Submission) and s.user_id == user_id]

    def list_by_test(self, test_id: str) -> List[Submission]:
        return [self._clone(s) for s in self._items.values() if isinstance(s, Submission) and s.test_id == test_id]

    def average_score_for_test(self, test_id: str) -> Optional[float]:
        scores = [s.score for s in self._items.values() if isinstance(s, Submission) and s.test_id == test_id and s.score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def completion_rate_for_test(self, test_id: str) -> float:
        subs = [s for s in self._items.values() if isinstance(s, Submission) and s.test_id == test_id]
        if not subs:
            return 0.0
        completed = sum(1 for s in subs if s.status in {"submitted", "graded"})
        return completed / len(subs)

    def top_scores_for_test(self, test_id: str, n: int = 5) -> List[Tuple[str, float]]:
        """
        Return top n scores for a test as (submission_id, score). Ignores None scores.
        """
        scored = [(s.id, s.score) for s in self._items.values() if isinstance(s, Submission) and s.test_id == test_id and s.score is not None]  # type: ignore[return-value]
        scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)  # type: ignore[index]
        return scored_sorted[:n]

    def user_average_score(self, user_id: str) -> Optional[float]:
        scores = [s.score for s in self._items.values() if isinstance(s, Submission) and s.user_id == user_id and s.score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)


class InMemoryUnitOfWork:
    """
    Simple Unit of Work to hold repository instances.

    This allows routes/services to accept a single dependency and makes it easier
    to swap underlying implementations later.
    """

    def __init__(
        self,
        users: Optional[InMemoryUserRepository] = None,
        tests: Optional[InMemoryTestRepository] = None,
        submissions: Optional[InMemorySubmissionRepository] = None,
    ) -> None:
        self.users = users or InMemoryUserRepository()
        self.tests = tests or InMemoryTestRepository()
        self.submissions = submissions or InMemorySubmissionRepository()

    # PUBLIC_INTERFACE
    def seed_demo_data(self) -> Dict[str, Any]:
        """
        Seed the repositories with minimal demo data for development and testing.

        Returns:
            A dict containing ids of created entities for quick reference.
        """
        # Create users
        author = User(email="author@example.com", name="Author One", role="author")
        student = User(email="student@example.com", name="Student One", role="student")
        self.users.create(author)
        self.users.create(student)

        # Create a test
        test = Test(
            title="Sample Math Test",
            description="Basic arithmetic questions",
            author_id=author.id,
            published=True,
            tags=["math", "arithmetic"],
            questions=[
                {"id": "q1", "prompt": "2 + 2 = ?", "type": "single_choice", "options": ["3", "4", "5"], "answer": "4"},
                {"id": "q2", "prompt": "5 - 3 = ?", "type": "short_answer", "answer": "2"},
            ],
        )
        self.tests.create(test)

        # Create a submission
        sub = Submission(
            test_id=test.id,
            user_id=student.id,
            answers={"q1": "4", "q2": "2"},
            score=100.0,
            status="graded",
            duration_seconds=75,
        )
        self.submissions.create(sub)

        return {"author_id": author.id, "student_id": student.id, "test_id": test.id, "submission_id": sub.id}
