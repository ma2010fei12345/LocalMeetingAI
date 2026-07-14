import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import DB_PATH, DEFAULT_PROJECT_NAME, ensure_data_dirs


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            create table if not exists projects (
                id integer primary key autoincrement,
                name text not null unique,
                description text not null default '',
                created_at text not null
            );

            create table if not exists documents (
                id integer primary key autoincrement,
                project_id integer not null,
                filename text not null,
                encrypted_path text not null,
                size_bytes integer not null,
                chunk_count integer not null default 0,
                created_at text not null,
                foreign key(project_id) references projects(id) on delete cascade
            );

            create table if not exists transcript_events (
                id integer primary key autoincrement,
                project_id integer not null,
                speaker text not null,
                text text not null,
                confidence real not null default 0,
                created_at text not null,
                foreign key(project_id) references projects(id) on delete cascade
            );

            create table if not exists ai_events (
                id integer primary key autoincrement,
                project_id integer not null,
                trigger_type text not null,
                content text not null,
                sources text not null default '[]',
                created_at text not null,
                foreign key(project_id) references projects(id) on delete cascade
            );
            """
        )
        exists = conn.execute("select id from projects limit 1").fetchone()
        if not exists:
            conn.execute(
                "insert into projects(name, description, created_at) values (?, ?, ?)",
                (DEFAULT_PROJECT_NAME, "本地单机会议项目", utc_now()),
            )


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def resolve_path(value: str) -> Path:
    return Path(value).resolve()
