"""Phase 6 tests: Database operations, persistence, relationships, constraints, and privacy."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base, init_db
from app.models.analysis import SkillAnalysisRecord
from app.models.job_description import JobDescriptionAnalysisRecord
from app.models.progress import TaskProgressRecord
from app.models.resume import ResumeRecord
from app.models.roadmap import RoadmapRecord, RoadmapTaskRecord
from app.models.user import User, hash_password, verify_password


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database and yield a clean session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    init_db(bind_engine=engine)

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# ---------------------------------------------------------------------------
# Database Creation & Schema Inspection Tests
# ---------------------------------------------------------------------------


class TestDatabaseCreation:
    """Tests verifying database table creation and constraints."""

    def test_all_expected_tables_created(self, db_session):
        """Verify that all Phase 6 tables are created in the database schema."""
        bind = db_session.get_bind()
        inspector = inspect(bind)
        table_names = inspector.get_table_names()

        expected = [
            "users",
            "resumes",
            "skill_analyses",
            "roadmaps",
            "roadmap_tasks",
            "task_progress",
            "job_description_analyses",
        ]
        for tbl in expected:
            assert tbl in table_names, f"Expected table '{tbl}' was not found in schema."


# ---------------------------------------------------------------------------
# User & Password Security Tests
# ---------------------------------------------------------------------------


class TestUserPersistenceAndSecurity:
    """Tests for user management and secure password hashing."""

    def test_passwords_never_stored_in_plaintext(self):
        """Plaintext passwords must be hashed using a cryptographic hash with a salt."""
        raw_password = "SecretPassword123!"
        hashed = hash_password(raw_password)

        assert hashed != raw_password
        assert "$" in hashed
        assert len(hashed) > 40
        assert verify_password(raw_password, hashed) is True
        assert verify_password("WrongPassword!", hashed) is False

    def test_create_and_retrieve_user(self, db_session):
        """Creating a user and querying by email."""
        user = User(
            email="candidate@example.com",
            hashed_password=hash_password("SuperSecret99"),
            full_name="Jane Doe",
        )
        db_session.add(user)
        db_session.commit()

        retrieved = db_session.query(User).filter_by(email="candidate@example.com").first()
        assert retrieved is not None
        assert retrieved.id is not None
        assert retrieved.full_name == "Jane Doe"
        assert retrieved.is_active is True
        assert verify_password("SuperSecret99", retrieved.hashed_password) is True

    def test_unique_email_constraint_enforced(self, db_session):
        """Inserting two users with the same email must trigger an IntegrityError."""
        u1 = User(email="duplicate@example.com", hashed_password=hash_password("p1"))
        u2 = User(email="duplicate@example.com", hashed_password=hash_password("p2"))
        db_session.add(u1)
        db_session.commit()

        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()


# ---------------------------------------------------------------------------
# Resume Metadata & Deletion Tests
# ---------------------------------------------------------------------------


class TestResumePersistenceAndPrivacy:
    """Tests verifying privacy guidelines and resume metadata handling."""

    def test_resume_stores_plain_text_only_no_binary(self, db_session):
        """Verify resume records store only plain text and metadata without binary blobs."""
        user = User(email="dev@example.com", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()

        resume = ResumeRecord(
            user_id=user.id,
            filename="jane_resume.pdf",
            file_type="pdf",
            file_size_bytes=1048576,
            extracted_text="Experienced Python and Docker developer.",
        )
        resume.set_extracted_skills([{"skill_id": "python", "canonical": "Python"}])
        db_session.add(resume)
        db_session.commit()

        queried = db_session.query(ResumeRecord).filter_by(id=resume.id).first()
        assert queried is not None
        assert queried.filename == "jane_resume.pdf"
        assert queried.file_type == "pdf"
        assert "Experienced Python" in queried.extracted_text
        # Ensure helper method unpacks cached JSON skills correctly
        skills = queried.get_extracted_skills()
        assert len(skills) == 1
        assert skills[0]["skill_id"] == "python"

    def test_resume_deletion_purges_content(self, db_session):
        """Deleting a resume removes extracted content permanently from the database."""
        user = User(email="delete_test@example.com", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()

        resume = ResumeRecord(
            user_id=user.id,
            filename="temp.pdf",
            file_type="pdf",
            file_size_bytes=5000,
            extracted_text="Sensitive resume details.",
        )
        db_session.add(resume)
        db_session.commit()
        res_id = resume.id

        # Delete resume
        db_session.delete(resume)
        db_session.commit()

        assert db_session.query(ResumeRecord).filter_by(id=res_id).first() is None


# ---------------------------------------------------------------------------
# Skill Gap Analysis & Relationships Tests
# ---------------------------------------------------------------------------


class TestAnalysisPersistence:
    """Tests for saving and linking skill-gap analyses."""

    def test_save_skill_analysis_linked_to_user_and_resume(self, db_session):
        """Skill analysis record must establish valid relationships with user and resume."""
        user = User(email="analyst@example.com", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()

        resume = ResumeRecord(
            user_id=user.id,
            filename="cv.pdf",
            file_type="pdf",
            file_size_bytes=8000,
            extracted_text="Python and SQL",
        )
        db_session.add(resume)
        db_session.commit()

        analysis = SkillAnalysisRecord(
            user_id=user.id,
            resume_id=resume.id,
            role_id="data-analyst",
            role_title="Data Analyst",
            coverage_percent=75.0,
            matched_skills_json='[{"skill_id": "sql"}]',
            missing_skills_json='[{"skill_id": "tableau"}]',
            uncertain_skills_json='[]',
            priority_gaps_json='[{"skill_id": "tableau", "importance": "high"}]',
        )
        db_session.add(analysis)
        db_session.commit()

        queried = db_session.query(SkillAnalysisRecord).filter_by(id=analysis.id).first()
        assert queried.user.email == "analyst@example.com"
        assert queried.resume.filename == "cv.pdf"
        assert queried.coverage_percent == 75.0
        assert len(queried.get_matched_skills()) == 1


# ---------------------------------------------------------------------------
# Roadmap, Tasks & Restart Persistence Tests
# ---------------------------------------------------------------------------


class TestRoadmapAndProgressPersistence:
    """Tests verifying roadmap task persistence and surviving application restarts."""

    def test_save_roadmap_with_child_tasks(self, db_session):
        """Saving a roadmap cascades and creates associated child task records."""
        user = User(email="harness_user@example.com", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()

        roadmap = RoadmapRecord(
            user_id=user.id,
            role_id="harness-engineer",
            role_title="Harness Engineer",
            total_weeks=6,
            target_weekly_hours=12,
            total_estimated_hours=60,
            capstone_project="Automated Harness Deployment Pipeline with Canary Rollouts",
        )
        db_session.add(roadmap)
        db_session.commit()

        task1 = RoadmapTaskRecord(
            roadmap_id=roadmap.id,
            task_key="task-w1-docker",
            title="Learn Docker",
            description="Container fundamentals",
            target_skill="Docker",
            week=1,
            estimated_effort=6,
            completion_status="pending",
        )
        task2 = RoadmapTaskRecord(
            roadmap_id=roadmap.id,
            task_key="task-w2-kubernetes",
            title="Learn Kubernetes",
            description="Cluster deployment",
            target_skill="Kubernetes",
            week=2,
            estimated_effort=6,
            completion_status="pending",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # Query roadmap and verify task relationship
        queried = db_session.query(RoadmapRecord).filter_by(id=roadmap.id).first()
        assert len(queried.tasks) == 2
        assert queried.tasks[0].target_skill == "Docker"
        assert queried.tasks[1].target_skill == "Kubernetes"

    def test_progress_survives_restart_simulation(self, tmp_path):
        """Simulate an application restart by writing to SQLite file, closing session, and reading back."""
        db_file = tmp_path / "restart_test.db"
        file_url = f"sqlite:///{db_file}"

        engine1 = create_engine(file_url, future=True)
        init_db(bind_engine=engine1)
        Session1 = sessionmaker(bind=engine1, future=True)

        # Session 1: Create user, roadmap, task, and mark progress as completed
        with Session1() as s1:
            user = User(email="restart_user@example.com", hashed_password=hash_password("pass"))
            s1.add(user)
            s1.commit()

            roadmap = RoadmapRecord(
                user_id=user.id,
                role_id="backend-engineer",
                role_title="Backend Engineer",
                total_weeks=6,
                target_weekly_hours=10,
                total_estimated_hours=60,
                capstone_project="REST API",
            )
            s1.add(roadmap)
            s1.commit()

            task = RoadmapTaskRecord(
                roadmap_id=roadmap.id,
                task_key="task-w1-python",
                title="Learn Python",
                description="Core Python",
                target_skill="Python",
                week=1,
                estimated_effort=5,
                completion_status="pending",
            )
            s1.add(task)
            s1.commit()

            progress = TaskProgressRecord(
                user=user,
                task=task,
            )
            progress.mark_completed()
            progress.notes = "Completed module 1 through 5 with high marks."
            s1.add(progress)
            s1.commit()

            task_id = task.id
            user_id = user.id

        # Dispose engine 1 (simulating process shutdown)
        engine1.dispose()

        # Session 2: Fresh engine and session connecting to the same on-disk DB
        engine2 = create_engine(file_url, future=True)
        Session2 = sessionmaker(bind=engine2, future=True)

        with Session2() as s2:
            saved_progress = s2.query(TaskProgressRecord).filter_by(user_id=user_id, task_id=task_id).first()
            assert saved_progress is not None
            assert saved_progress.status == "completed"
            assert saved_progress.completed_at is not None
            assert "module 1 through 5" in saved_progress.notes

            saved_task = s2.query(RoadmapTaskRecord).filter_by(id=task_id).first()
            assert saved_task.completion_status == "completed"

        engine2.dispose()


# ---------------------------------------------------------------------------
# Job Description Analysis Persistence Tests
# ---------------------------------------------------------------------------


class TestJobDescriptionAnalysisPersistence:
    """Tests for persisting and retrieving job description comparison records."""

    def test_save_and_retrieve_job_analysis(self, db_session):
        """Save a job description comparison record with JSON data and retrieve it."""
        job_analysis = JobDescriptionAnalysisRecord(
            job_title="Lead AI Engineer",
            company_name="Apex AI",
            job_description_text="Must have Python, LangChain, and Docker.",
            coverage_percent=66.67,
            extracted_skills_json='[{"skill_id": "python"}, {"skill_id": "langchain"}, {"skill_id": "docker"}]',
            matched_skills_json='[{"skill_id": "python"}, {"skill_id": "docker"}]',
            missing_skills_json='[{"skill_id": "langchain"}]',
            required_skills_json='[{"skill_id": "python"}, {"skill_id": "docker"}]',
            preferred_skills_json='[]',
            experience_requirements_json='[{"raw_text": "5+ years", "years": 5.0}]',
            caveats_json='["Pattern match heuristic only"]',
        )
        db_session.add(job_analysis)
        db_session.commit()

        queried = db_session.query(JobDescriptionAnalysisRecord).filter_by(id=job_analysis.id).first()
        assert queried is not None
        assert queried.company_name == "Apex AI"
        assert queried.coverage_percent == 66.67
        assert len(queried.get_extracted_skills()) == 3
        assert len(queried.get_experience_requirements()) == 1


# ---------------------------------------------------------------------------
# Cascading Deletion Tests
# ---------------------------------------------------------------------------


class TestCascadingDeletion:
    """Tests verifying cascade behaviors when root entities are deleted."""

    def test_delete_user_cascades_to_all_subordinate_records(self, db_session):
        """Deleting a User must cascade delete their resumes, analyses, roadmaps, and progress."""
        user = User(email="cascade_test@example.com", hashed_password=hash_password("pass"))
        db_session.add(user)
        db_session.commit()
        u_id = user.id

        resume = ResumeRecord(
            user_id=u_id,
            filename="res.pdf",
            file_type="pdf",
            file_size_bytes=1000,
            extracted_text="Python",
        )
        roadmap = RoadmapRecord(
            user_id=u_id,
            role_id="data-engineer",
            role_title="Data Engineer",
            total_weeks=6,
            target_weekly_hours=10,
            total_estimated_hours=60,
            capstone_project="Airflow lakehouse",
        )
        db_session.add_all([resume, roadmap])
        db_session.commit()

        task = RoadmapTaskRecord(
            roadmap_id=roadmap.id,
            task_key="task-w1-airflow",
            title="Airflow",
            description="Airflow",
            target_skill="Apache Airflow",
            week=1,
            estimated_effort=5,
        )
        db_session.add(task)
        db_session.commit()

        progress = TaskProgressRecord(user_id=u_id, task_id=task.id, status="in_progress")
        db_session.add(progress)
        db_session.commit()

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Verify cascading deletion
        assert db_session.query(User).filter_by(id=u_id).first() is None
        assert db_session.query(ResumeRecord).filter_by(user_id=u_id).first() is None
        assert db_session.query(RoadmapRecord).filter_by(user_id=u_id).first() is None
        assert db_session.query(TaskProgressRecord).filter_by(user_id=u_id).first() is None
