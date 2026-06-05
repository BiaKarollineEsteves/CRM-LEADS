"""utils/db.py — Neon PostgreSQL"""
import psycopg2
import psycopg2.extras
import psycopg2.pool
import streamlit as st
from contextlib import contextmanager


@st.cache_resource
def _pool():
    url = st.secrets["neon"]["database_url"]
    return psycopg2.pool.ThreadedConnectionPool(
        1, 5, dsn=url,
        cursor_factory=psycopg2.extras.RealDictCursor
    )


@contextmanager
def db():
    pool = _pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        pool.putconn(conn)


def Q(sql, params=()):
    with db() as conn:
        with conn.cursor() as c:
            c.execute(sql, params)
            rows = c.fetchall()
            return [dict(r) for r in rows] if rows else []


def Q1(sql, params=()):
    with db() as conn:
        with conn.cursor() as c:
            c.execute(sql, params)
            r = c.fetchone()
            return dict(r) if r else None


def X(sql, params=()):
    with db() as conn:
        with conn.cursor() as c:
            c.execute(sql, params)


def XM(sql, rows):
    with db() as conn:
        with conn.cursor() as c:
            psycopg2.extras.execute_batch(c, sql, rows)
