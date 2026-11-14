"""Authentication and User Management Schemas."""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""

    email: str = Field(..., description="Unique email address for user registration.")
    password: str = Field(..., min_length=8, description="Plaintext password (min 8 characters).")
    full_name: Optional[str] = Field(None, description="Candidate or developer full name.")
    name: Optional[str] = Field(None, description="Alternative name parameter for architecture alignment.")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError("Invalid email address format.")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v.strip()) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v

    def get_effective_name(self) -> Optional[str]:
        return (self.full_name or self.name or "").strip() or None


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""

    email: str = Field(..., description="Registered email address.")
    password: str = Field(..., description="Account password.")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError("Invalid email address format.")
        return trimmed


class UserResponse(BaseModel):
    """User profile response model."""

    id: int = Field(..., description="User unique identifier.")
    email: str = Field(..., description="Registered email address.")
    full_name: Optional[str] = Field(None, description="Full name.")
    name: Optional[str] = Field(None, description="Display name alias.")
    education_stage: Optional[str] = Field(None, description="Education stage.")
    career_interests: Optional[str] = Field(None, description="Career interests.")
    skill_level: Optional[str] = Field(None, description="Skill level.")
    target_role: Optional[str] = Field(None, description="Target role ID.")
    secondary_role: Optional[str] = Field(None, description="Secondary/comparison target role ID.")
    github_username: Optional[str] = Field(None, description="GitHub username.")
    leetcode_username: Optional[str] = Field(None, description="LeetCode username.")
    coding_signal_json: Optional[str] = Field(None, description="Persisted coding profile signal JSON.")
    onboarding_completed: bool = Field(False, description="Whether onboarding has been completed.")
    is_active: bool = Field(True, description="Account active status.")
    created_at: Optional[datetime] = Field(None, description="Timestamp of registration.")

    model_config = ConfigDict(from_attributes=True)


class UserOnboardingRequest(BaseModel):
    """Payload to save first-time user onboarding information."""

    full_name: Optional[str] = Field(None, description="Candidate or developer full name.")
    education_stage: Optional[str] = Field(None, description="Current education or professional stage.")
    career_interests: Optional[str] = Field(None, description="Career interests.")
    skill_level: Optional[str] = Field(None, description="Current skill level, if provided.")
    target_role: Optional[str] = Field(None, description="Initial target role ID.")
    secondary_role: Optional[str] = Field(None, description="Secondary/comparison target role ID.")


class TokenResponse(BaseModel):
    """Authentication token response matching both OAuth2 standard and architecture specs."""

    access_token: str = Field(..., description="Signed JSON Web Token string.")
    token_type: str = Field(default="bearer", description="Token type (Bearer).")
    token: str = Field(..., description="Alias token string for architecture client compatibility.")
    expires_in_minutes: int = Field(..., description="Token validity window in minutes.")
    user: UserResponse = Field(..., description="Authenticated user profile.")


class TaskStatusUpdateRequest(BaseModel):
    """Payload to update roadmap task completion status."""

    status: Optional[str] = Field(
        None,
        description="Task status: 'pending', 'in_progress', or 'completed'.",
    )
    done: Optional[bool] = Field(
        None,
        description="Boolean status flag for backward/frontend compatibility.",
    )
    notes: Optional[str] = Field(None, description="Optional personal notes on progress.")

    @field_validator("status")
    @classmethod
    def validate_status_value(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            normalized = v.strip().lower()
            if normalized not in {"pending", "in_progress", "completed"}:
                raise ValueError("Status must be one of: 'pending', 'in_progress', 'completed'.")
            return normalized
        return v


class TaskProgressItem(BaseModel):
    """Individual task progress information."""

    task_id: int
    task_key: str
    title: str
    target_skill: str
    week: int
    status: str
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class ProgressSummaryResponse(BaseModel):
    """Aggregated progress summary for the authenticated user."""

    user_id: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    completion_percentage: float
    active_roadmaps_count: int
    progress_items: List[TaskProgressItem] = Field(default_factory=list)


class ForgotPasswordRequest(BaseModel):
    """Payload to initiate a password reset link."""

    email: str = Field(..., description="Registered email address to receive reset instructions.")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError("Invalid email address format.")
        return trimmed


class ForgotPasswordResponse(BaseModel):
    """Generic response to prevent email enumeration attacks."""

    status: str = Field(default="success")
    message: str = Field(
        default="If an account with that email exists, we've sent password reset instructions to your inbox."
    )


class ResetPasswordRequest(BaseModel):
    """Payload to complete a password reset."""

    token: str = Field(..., min_length=16, description="Cryptographic reset token received via email.")
    new_password: str = Field(..., min_length=8, description="New strong password.")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z).")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one numeric digit (0-9).")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+[\]\\/`~;']", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&* etc.).")
        return v


class ResetPasswordResponse(BaseModel):
    """Confirmation response after successful password reset."""

    status: str = Field(default="success")
    message: str = Field(
        default="Password has been reset successfully. You can now sign in with your new password."
    )
