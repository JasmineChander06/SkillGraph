"""Automated tests for Resume Advisor & Rating Engine."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.resume_advisor import (
    audit_action_verbs,
    audit_brevity_and_fluff,
    audit_quantification,
    audit_technical_keywords,
    critique_resume_text,
)

client = TestClient(app)


def test_short_resume_returns_low_score_and_guidance():
    """Short or empty resumes must be scored appropriately with advice to expand."""
    res = critique_resume_text("Too short.")
    assert res.overall_score <= 20
    assert res.rating_label == "Needs Critical Revision"
    assert len(res.things_to_add) > 0


def test_fluff_words_detected_and_penalized():
    """Cliches like 'hardworking', 'team player', 'passionate' must be flagged in things_to_remove."""
    fluff_text = (
        "I am a hardworking and passionate team player with a go-getter attitude. "
        "Dynamic and fast learner who is detail-oriented and results-driven with good communication skills. "
        "Worked on backend tasks and responsible for team duties."
    )
    score, strengths, things_to_remove, fluff_list = audit_brevity_and_fluff(fluff_text)
    assert score < 15.0
    assert "hardworking" in fluff_list
    assert "team player" in fluff_list
    assert "detail-oriented" in fluff_list
    assert len(things_to_remove) >= 4


def test_clean_technical_text_has_high_clarity_score():
    """Technical text without buzzwords should receive high brevity/clarity score."""
    clean_text = (
        "Architected scalable microservices using Python, FastAPI, and PostgreSQL. "
        "Deployed Docker containers across Kubernetes clusters with automated CI/CD pipelines."
    )
    score, strengths, things_to_remove, fluff_list = audit_brevity_and_fluff(clean_text)
    assert score >= 24.0
    assert len(fluff_list) == 0
    assert len(things_to_remove) == 0


def test_quantification_detection():
    """Metrics such as percentages, latency figures, and user counts must be detected."""
    quant_text = (
        "Reduced p95 API latency by 45% (from 420ms to 230ms). "
        "Scaled backend services to handle 500k daily requests with 99.9% uptime, saving $40k annually."
    )
    score, strengths, additions = audit_quantification(quant_text)
    assert score >= 20.0
    assert len(strengths) > 0


def test_action_verbs_scoring():
    """Strong engineering verbs earn points; passive voice receives actionable critique."""
    active_text = "Architected, engineered, automated, benchmarked, deployed, and refactored core backend systems."
    score_active, _, _ = audit_action_verbs(active_text)
    assert score_active >= 20.0

    passive_text = "Responsible for backend tasks and assisted with database maintenance."
    score_passive, _, additions = audit_action_verbs(passive_text)
    assert score_passive < score_active
    assert any("Replace passive phrasing" in a for a in additions)


def test_technical_keyword_extraction():
    """Technical skills recognized by the ontology boost keyword density."""
    tech_text = "Proficient with Python, FastAPI, PostgreSQL, Redis, Docker, Git, and Kubernetes."
    score, strengths, additions = audit_technical_keywords(tech_text)
    assert score >= 20.0
    assert len(strengths) > 0


def test_high_impact_resume_scores_competitive_or_exceptional():
    """A quantified, technical, active resume should score competitive or exceptional."""
    resume_text = """
    Jane Doe | Senior Software Engineer | github.com/janedoe
    
    Experience:
    - Architected and engineered high-throughput REST APIs using Python, FastAPI, and PostgreSQL, handling 250k daily requests.
    - Automated CI/CD deployment pipelines using Docker and Kubernetes, reducing release cycle time by 60%.
    - Optimized Redis caching layer, decreasing database query load by 40% and cutting p95 response latency from 350ms to 110ms.
    - Spearheaded migration of legacy monolith to microservices, saving $50k in annual cloud infrastructure costs.
    - Implemented automated test suites with pytest achieving 92% coverage across 8 services.
    """
    res = critique_resume_text(resume_text)
    assert res.overall_score >= 80
    assert res.rating_label in ("Competitive", "Exceptional")
    assert len(res.strengths) >= 3
    assert len(res.bullet_improvements) > 0


def test_critique_endpoint_success():
    """POST /api/resume/critique responds with 200 and structured response."""
    payload = {
        "text": "Architected Python FastAPI backend with PostgreSQL and Docker. Scaled to 10k users with 99.9% uptime."
    }
    response = client.post("/api/resume/critique", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "overall_score" in data
    assert "rating_label" in data
    assert "dimension_scores" in data
    assert "strengths" in data
    assert "things_to_add" in data
    assert "things_to_remove" in data
    assert "bullet_improvements" in data
    assert "summary" in data


def test_critique_endpoint_empty_payload_returns_422():
    """POST /api/resume/critique with empty payload must return 422."""
    response = client.post("/api/resume/critique", json={})
    assert response.status_code == 422

