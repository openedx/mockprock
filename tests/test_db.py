import logging
import sqlite3

import pytest

from mockprock.db import DB, namedtuple_factory


@pytest.fixture
def db(tmp_path):
    instance = DB(str(tmp_path / "test.sqlite"), logging.getLogger(__name__))
    instance.setup()
    return instance


def test_save_and_get_exam(db):
    exam = {
        "course_id": "course-v1:test+test+test",
        "exam_name": "Test Exam",
        "is_practice_exam": False,
        "rules": {"allow_notes": True},
    }
    exam_id = db.save_exam(exam)
    assert exam_id is not None

    retrieved = db.get_exam(exam_id)
    assert retrieved["id"] == exam_id
    assert retrieved["name"] == "Test Exam"
    assert retrieved["course_id"] == "course-v1:test+test+test"
    assert retrieved["rules"] == {"allow_notes": True}


def test_save_exam_updates_existing(db):
    exam = {
        "course_id": "course-v1:test+test+test",
        "exam_name": "Original Name",
        "is_practice_exam": False,
        "rules": {},
    }
    exam_id = db.save_exam(exam)
    exam["external_id"] = exam_id
    exam["exam_name"] = "Updated Name"
    db.save_exam(exam)

    retrieved = db.get_exam(exam_id)
    assert retrieved["name"] == "Updated Name"


def test_get_exam_not_found(db):
    assert db.get_exam("nonexistent") == {}


def test_save_and_get_attempt(db):
    exam_id = db.save_exam(
        {
            "course_id": "course-v1:test+test+test",
            "exam_name": "Test Exam",
            "is_practice_exam": False,
            "rules": {},
        }
    )
    attempt = {
        "exam_id": exam_id,
        "status": "created",
        "user_id": "user1",
        "full_name": "Test User",
        "email": "test@example.com",
        "lms_host": "http://localhost:18000",
    }
    result = db.save_attempt(attempt)
    attempt_id = result["id"]

    retrieved = db.get_attempt(exam_id, attempt_id)
    assert retrieved["id"] == attempt_id
    assert retrieved["status"] == "created"
    assert retrieved["user_id"] == "user1"
    assert retrieved["email"] == "test@example.com"


def test_update_attempt_status(db):
    exam_id = db.save_exam(
        {
            "course_id": "course-v1:test+test+test",
            "exam_name": "Exam",
            "is_practice_exam": False,
            "rules": {},
        }
    )
    attempt = db.save_attempt(
        {
            "exam_id": exam_id,
            "status": "created",
            "user_id": "u1",
            "full_name": "User",
            "email": "u@example.com",
            "lms_host": "http://localhost:18000",
        }
    )
    attempt["status"] = "submitted"
    db.save_attempt(attempt)

    retrieved = db.get_attempt(exam_id, attempt["id"])
    assert retrieved["status"] == "submitted"


def test_get_attempt_not_found(db):
    assert db.get_attempt("exam1", "attempt1") == {}


def test_get_exams_by_course(db):
    course_id = "course-v1:test+test+test"
    for i in range(3):
        db.save_exam(
            {
                "course_id": course_id,
                "exam_name": f"Exam {i}",
                "is_practice_exam": False,
                "rules": {},
            }
        )
    db.save_exam(
        {
            "course_id": "other-course",
            "exam_name": "Other Exam",
            "is_practice_exam": False,
            "rules": {},
        }
    )

    exams = list(db.get_exams(course_id=course_id))
    assert len(exams) == 3
    assert all(e["course_id"] == course_id for e in exams)


def test_get_all_exams(db):
    for i in range(2):
        db.save_exam(
            {
                "course_id": f"course-{i}",
                "exam_name": "Exam",
                "is_practice_exam": False,
                "rules": {},
            }
        )
    exams = list(db.get_exams())
    assert len(exams) == 2


def test_namedtuple_factory():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'hello')")
    conn.row_factory = namedtuple_factory
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test")
    row = cursor.fetchone()
    assert row.id == 1
    assert row.name == "hello"
    conn.close()
