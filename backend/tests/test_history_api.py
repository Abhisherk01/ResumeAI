"""Cross-resume history endpoint tests (Phase 9 Step 1).

Pins the four contracts of the new read-only surface: newest-first
ordering across resumes WITH filenames attached, ownership scoping (user
B's history contains none of user A's rows even though both exist), the
fixed 50-cap (D20), and authentication. Rows are inserted directly with
explicit timestamps so ordering is deterministic even under SQLite's
second-resolution CURRENT_TIMESTAMP.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from httpx import Response

from app.db.models.analysis import Analysis
from app.db.models.match import Match
from app.db.models.resume import Resume
from app.db.models.user import User

PASSWORD = "correct-horse-battery"


def _error_code(response: Response) -> str:
    body = response.json()
    assert set(body) == {"error"}, f"expected error envelope, got: {body}"
    return body["error"]["code"]


def _register_verify_login(
    client: TestClient, outbox, *, email: str = "user@example.com"
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "name": "Test User"},
    )
    body = outbox.messages[-1].body
    start = body.index("token=") + len("token=")
    token = body[start:].split()[0]
    client.post("/api/v1/auth/verify-email", json={"token": token})
    client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )


def _user_id(db, email: str) -> uuid.UUID:
    user = db.query(User).filter_by(email=email).one()
    return user.id


def _insert_resume(db, *, user_id: uuid.UUID, filename: str) -> Resume:
    resume = Resume(
        user_id=user_id,
        filename=filename,
        content_type="application/pdf",
        file_size=10,
        file_data=b"x",
    )
    db.add(resume)
    db.flush()
    return resume


def _insert_analysis(
    db, *, user_id: uuid.UUID, resume_id: uuid.UUID, score: int, created_at
) -> None:
    db.add(
        Analysis(
            resume_id=resume_id,
            user_id=user_id,
            score=score,
            scoring_version="v1",
            score_breakdown={},
            strengths=[],
            improvements=[],
            provider="mock",
            created_at=created_at,
        )
    )


def _insert_match(
    db,
    *,
    user_id: uuid.UUID,
    resume_id: uuid.UUID,
    score: int,
    title: str,
    created_at,
) -> None:
    db.add(
        Match(
            resume_id=resume_id,
            user_id=user_id,
            job_description="A job description long enough for the schema.",
            job_title=title,
            match_score=score,
            matching_version="mv1",
            match_breakdown={},
            matched_keywords=[],
            missing_keywords=[],
            provider="mock",
            suggestions={"strengths": [], "improvements": []},
            created_at=created_at,
        )
    )


def test_analyses_history_newest_first_with_filenames(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    old = _insert_resume(db, user_id=uid, filename="old.docx")
    new = _insert_resume(db, user_id=uid, filename="new.docx")
    now = datetime.now(UTC)
    _insert_analysis(
        db, user_id=uid, resume_id=old.id, score=40,
        created_at=now - timedelta(hours=2),
    )
    _insert_analysis(
        db, user_id=uid, resume_id=new.id, score=90,
        created_at=now - timedelta(hours=1),
    )
    db.commit()

    response = client.get("/api/v1/analyses")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert [row["score"] for row in rows] == [90, 40]
    assert [row["resume_filename"] for row in rows] == ["new.docx", "old.docx"]


def test_matches_history_newest_first_with_filenames(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    resume = _insert_resume(db, user_id=uid, filename="cv.docx")
    now = datetime.now(UTC)
    _insert_match(
        db, user_id=uid, resume_id=resume.id, score=55,
        title="Old role", created_at=now - timedelta(hours=2),
    )
    _insert_match(
        db, user_id=uid, resume_id=resume.id, score=80,
        title="New role", created_at=now - timedelta(hours=1),
    )
    db.commit()

    response = client.get("/api/v1/matches")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert [row["match_score"] for row in rows] == [80, 55]
    assert [row["job_title"] for row in rows] == ["New role", "Old role"]
    assert all(row["resume_filename"] == "cv.docx" for row in rows)


def test_history_is_scoped_to_the_owner(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid_a = _user_id(db, "user@example.com")
    resume_a = _insert_resume(db, user_id=uid_a, filename="secret.docx")
    now = datetime.now(UTC)
    _insert_analysis(
        db, user_id=uid_a, resume_id=resume_a.id, score=90, created_at=now
    )
    _insert_match(
        db, user_id=uid_a, resume_id=resume_a.id, score=90,
        title="A's role", created_at=now,
    )
    db.commit()

    # User B sees none of A's rows - the rows exist, they are just
    # unreachable by construction (the IDOR posture, list edition).
    _register_verify_login(client, email_outbox, email="other@example.com")
    assert client.get("/api/v1/analyses").json() == []
    assert client.get("/api/v1/matches").json() == []

    # B's own rows come back - and only B's:
    uid_b = _user_id(db, "other@example.com")
    resume_b = _insert_resume(db, user_id=uid_b, filename="mine.docx")
    _insert_analysis(
        db, user_id=uid_b, resume_id=resume_b.id, score=70, created_at=now
    )
    _insert_match(
        db, user_id=uid_b, resume_id=resume_b.id, score=70,
        title="B's role", created_at=now,
    )
    db.commit()

    analyses = client.get("/api/v1/analyses").json()
    matches = client.get("/api/v1/matches").json()
    assert [row["resume_filename"] for row in analyses] == ["mine.docx"]
    assert [row["job_title"] for row in matches] == ["B's role"]


def test_history_caps_at_the_latest_50(client, email_outbox, db):
    _register_verify_login(client, email_outbox)
    uid = _user_id(db, "user@example.com")
    resume = _insert_resume(db, user_id=uid, filename="bulk.docx")
    now = datetime.now(UTC)
    for index in range(55):
        _insert_analysis(
            db,
            user_id=uid,
            resume_id=resume.id,
            score=index,
            created_at=now - timedelta(minutes=60 - index),
        )
    db.commit()

    rows = client.get("/api/v1/analyses").json()

    assert len(rows) == 50
    assert rows[0]["score"] == 54  # the newest, not an arbitrary 50


def test_history_requires_authentication(client):
    for path in ("/api/v1/analyses", "/api/v1/matches"):
        response = client.get(path)
        assert response.status_code == 401
        assert _error_code(response) == "not_authenticated"
