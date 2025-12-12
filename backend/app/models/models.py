import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


def create_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def _utcnow_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class BaseModel:
    """
    Base model with common timestamp fields and conversion helpers.
    """
    id: str = field(default_factory=create_uuid)
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = _utcnow_iso()

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict representation of the model."""
        return asdict(self)


@dataclass
class User(BaseModel):
    """
    Represents a platform user.
    """
    email: str = ""
    name: str = ""
    role: str = "author"  # e.g., 'author', 'student', 'admin'
    active: bool = True

    def validate(self) -> None:
        """Validate the user fields."""
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email for User")
        if not self.name:
            raise ValueError("User name is required")
        if self.role not in {"author", "student", "admin"}:
            raise ValueError("Invalid user role")


@dataclass
class Test(BaseModel):
    """
    Represents a digital test/assessment authored by a user.
    """
    title: str = ""
    description: str = ""
    author_id: str = ""
    # simple representation for questions: list of dicts {id, prompt, type, options?, answer?}
    questions: List[Dict[str, Any]] = field(default_factory=list)
    published: bool = False
    tags: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validate test fields."""
        if not self.title:
            raise ValueError("Test title is required")
        if not self.author_id:
            raise ValueError("Test author_id is required")


@dataclass
class Submission(BaseModel):
    """
    Represents a submission of answers to a Test by a User.
    """
    test_id: str = ""
    user_id: str = ""
    # answers: dict question_id -> answer value
    answers: Dict[str, Any] = field(default_factory=dict)
    # score may be computed or provided; keep optional
    score: Optional[float] = None
    # status: 'in_progress', 'submitted', 'graded'
    status: str = "submitted"
    # Optional AI evaluation metadata
    evaluation_notes: Optional[str] = None
    duration_seconds: Optional[int] = None

    def validate(self) -> None:
        """Validate submission fields."""
        if not self.test_id:
            raise ValueError("Submission requires test_id")
        if not self.user_id:
            raise ValueError("Submission requires user_id")
        if self.status not in {"in_progress", "submitted", "graded"}:
            raise ValueError("Invalid submission status")

