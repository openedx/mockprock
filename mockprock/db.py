from collections import namedtuple
from contextlib import closing
import json
import sqlite3
import uuid


def namedtuple_factory(cursor, row):
    """Returns sqlite rows as named tuples."""
    fields = [col[0] for col in cursor.description]
    Row = namedtuple("Row", fields)
    return Row(*row)

def init_app(app):
    app.db = DB('mockprock.sqlite', app.logger)
    app.db.setup()


class DB(object):
    def __init__(self, dbpath, logger):
        self.dbpath = dbpath
        self.logger = logger

    def connect(self):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = namedtuple_factory
        return conn

    def setup(self):
        create_sql = '''
        CREATE TABLE IF NOT EXISTS exams (
            id TEXT PRIMARY KEY,
            course_id TEXT,
            name TEXT,
            is_practice BOOL,
            rules TEXT,
            created TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attempts (
            id TEXT PRIMARY KEY,
            exam_id TEXT,
            status TEXT,
            user_id TEXT,
            user_name TEXT,
            user_email TEXT,
            created TIMESTAMP,
            modified TIMESTAMP,
            lms_host TEXT
        );'''.split(';')
        with self.connect() as conn:
            for stmt in create_sql:
                conn.execute(stmt)

    def get_exam(self, exam_id):
        with self.connect() as conn:
            with closing(conn.cursor()) as c:
                c.execute('select * from exams where id = ?', (exam_id,))
                row = c.fetchone()
                if row:
                    return {
                        'id': row.id,
                        'name': row.name,
                        'course_id': row.course_id,
                        'rules': json.loads(row.rules),
                    }
        return {}

    def save_exam(self, exam, client_id=None):
        rules = exam.get('rules', {})
        rules = json.dumps(rules)
        exam_id = exam.get('external_id', None)
        if not exam_id:
            exam_id = exam['external_id'] = uuid.uuid4().hex
        with self.connect() as conn:
            pars = (exam_id, exam['course_id'], exam['exam_name'], exam['is_practice_exam'], rules)
            try:
                conn.execute("insert into exams (id, course_id, name, is_practice, rules, created) values (?, ?, ?, ?, ?, datetime('now'))", pars)
                self.logger.info('Saved exam %s from %s', exam_id, client_id)
            except sqlite3.IntegrityError:
                pars = (exam['course_id'], exam['exam_name'], exam['is_practice_exam'], rules, exam_id)
                stmt = 'update exams set course_id = ?, name = ?, is_practice = ?, rules = ? where id = ?'
                conn.execute(stmt, pars)
                self.logger.info('Updated exam %s from %s', exam_id, client_id)
        return exam_id

    def get_attempt(self, exam_id, attempt_id):
        with self.connect() as conn:
            with closing(conn.cursor()) as c:
                c.execute('select id, status, exam_id, lms_host, user_id, user_email from attempts where id = ? and exam_id = ?', (attempt_id, exam_id))
                row = c.fetchone()
                if row:
                    return {
                        'id': row.id,
                        'status': row.status,
                        'exam_id': row.exam_id,
                        'lms_host': row.lms_host,
                        'user_id': row.user_id,
                        'email': row.user_email,
                    }
        return {}

    def save_attempt(self, attempt):
        attempt_id = attempt.get('id', None)
        if attempt_id:
            stmt = "update attempts set status = ?, modified = datetime('now') where id = ?"
            pars = (attempt['status'], attempt_id)
        else:
            attempt_id = attempt['id'] = uuid.uuid4().hex
            stmt = """insert into attempts (id, exam_id, status, user_id, user_name, user_email, lms_host, created, modified) 
            values (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))"""
            pars = (attempt_id, attempt['exam_id'], attempt['status'], attempt['user_id'],
                attempt['full_name'], attempt['email'], attempt['lms_host'])
        with self.connect() as conn:
            conn.execute(stmt, pars)
        self.logger.info('Created attempt %s from %r', attempt_id, attempt)
        return attempt

    def get_exams(self, course_id=None):
        if course_id:
            stmt, pars = 'select * from exams where course_id = ?', [course_id]
        else:
            stmt, pars = 'select * from exams', []
        with self.connect() as conn:
            with closing(conn.cursor()) as c:
                c.execute(stmt, pars)
                for row in c:
                    yield {
                        'id': row.id,
                        'name': row.name,
                        'course_id': row.course_id,
                        'is_practice': row.is_practice,
                        'rules': json.loads(row.rules),
                        'created': row.created
                    }
