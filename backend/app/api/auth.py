"""Authentication API endpoints for registration, login, and user profile management."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserOnboardingRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    register_user,
)

logger = logging.getLogger("skillgraph.api.auth")

router = APIRouter(tags=["Authentication"])


def _build_token_response(user: User) -> TokenResponse:
    """Helper to build token response payload for an authenticated user."""
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        name=user.full_name,
        education_stage=user.education_stage,
        career_interests=user.career_interests,
        skill_level=user.skill_level,
        target_role=user.target_role,
        secondary_role=user.secondary_role,
        github_username=user.github_username,
        leetcode_username=user.leetcode_username,
        coding_signal_json=user.coding_signal_json,
        onboarding_completed=user.onboarding_completed,
        is_active=user.is_active,
        created_at=user.created_at,
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        token=access_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_response,
    )


# Registration endpoints (supporting both /api/auth/register and /auth/signup)
@router.post(
    "/api/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@router.post(
    "/auth/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/api/auth/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Create a new candidate account with a securely hashed password.

    Returns the new user record along with an immediate authenticated session token.
    """
    user = register_user(
        db=db,
        email=request.email,
        password=request.password,
        full_name=request.get_effective_name(),
    )
    logger.info("Registered new user with ID %s", user.id)
    return _build_token_response(user)


# Login endpoints (supporting both /api/auth/login and /auth/login)
@router.post(
    "/api/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue access token",
)
@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate with registered email and password to receive a signed JWT token."""
    user = authenticate_user(
        db=db,
        email=request.email,
        password=request.password,
    )
    logger.info("User ID %s authenticated successfully", user.id)
    return _build_token_response(user)


# Current User Profile
@router.get(
    "/api/auth/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile",
)
@router.get(
    "/auth/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve the profile data of the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        name=current_user.full_name,
        education_stage=current_user.education_stage,
        career_interests=current_user.career_interests,
        skill_level=current_user.skill_level,
        target_role=current_user.target_role,
        secondary_role=current_user.secondary_role,
        github_username=current_user.github_username,
        leetcode_username=current_user.leetcode_username,
        coding_signal_json=current_user.coding_signal_json,
        onboarding_completed=current_user.onboarding_completed,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


# First-Time User Onboarding Endpoints
@router.post(
    "/api/auth/onboarding",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Save First-Time Onboarding Profile",
)
@router.post(
    "/api/user/onboarding",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def save_onboarding(
    payload: UserOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Save user onboarding info (education stage, career interests, skill level, target role)."""
    if payload.full_name is not None and payload.full_name.strip():
        current_user.full_name = payload.full_name.strip()
    if payload.education_stage is not None:
        current_user.education_stage = payload.education_stage.strip()
    if payload.career_interests is not None:
        current_user.career_interests = payload.career_interests.strip()
    if payload.skill_level is not None:
        current_user.skill_level = payload.skill_level.strip()
    if payload.target_role is not None:
        current_user.target_role = payload.target_role.strip()
    if payload.secondary_role is not None:
        current_user.secondary_role = payload.secondary_role.strip()

    current_user.onboarding_completed = True
    db.commit()
    db.refresh(current_user)

    logger.info("Saved onboarding for User ID %s", current_user.id)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        name=current_user.full_name,
        education_stage=current_user.education_stage,
        career_interests=current_user.career_interests,
        skill_level=current_user.skill_level,
        target_role=current_user.target_role,
        secondary_role=current_user.secondary_role,
        github_username=current_user.github_username,
        leetcode_username=current_user.leetcode_username,
        coding_signal_json=current_user.coding_signal_json,
        onboarding_completed=current_user.onboarding_completed,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.get(
    "/api/user/onboarding",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Onboarding Profile",
)
async def get_onboarding(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve onboarding profile data for the authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        name=current_user.full_name,
        education_stage=current_user.education_stage,
        career_interests=current_user.career_interests,
        skill_level=current_user.skill_level,
        target_role=current_user.target_role,
        secondary_role=current_user.secondary_role,
        github_username=current_user.github_username,
        leetcode_username=current_user.leetcode_username,
        coding_signal_json=current_user.coding_signal_json,
        onboarding_completed=current_user.onboarding_completed,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.put(
    "/api/user/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
)
async def update_profile(
    payload: UserOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update profile information for the authenticated user."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() or None
    if payload.education_stage is not None:
        current_user.education_stage = payload.education_stage.strip() or None
    if payload.career_interests is not None:
        current_user.career_interests = payload.career_interests.strip() or None
    if payload.skill_level is not None:
        current_user.skill_level = payload.skill_level.strip() or None
    if payload.target_role is not None:
        current_user.target_role = payload.target_role.strip() or None
    if payload.secondary_role is not None:
        current_user.secondary_role = payload.secondary_role.strip() or None

    db.commit()
    db.refresh(current_user)
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        name=current_user.full_name,
        education_stage=current_user.education_stage,
        career_interests=current_user.career_interests,
        skill_level=current_user.skill_level,
        target_role=current_user.target_role,
        secondary_role=current_user.secondary_role,
        github_username=current_user.github_username,
        leetcode_username=current_user.leetcode_username,
        coding_signal_json=current_user.coding_signal_json,
        onboarding_completed=current_user.onboarding_completed,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )

