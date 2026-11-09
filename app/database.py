import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "email_assistant.db",
)


def get_connection():
    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True,
    )

    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()

    cursor = conn.cursor()

    # Emails table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT UNIQUE NOT NULL,
            thread_id TEXT,
            sender TEXT,
            subject TEXT,
            received_at TEXT,
            processed_at TEXT,
            summary TEXT,
            importance TEXT,
            action_required INTEGER
        )
        """
    )

    # Runs table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT,
            completed_at TEXT,
            status TEXT,
            emails_processed INTEGER,
            error TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def is_email_processed(email_id: str) -> bool:
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM emails
        WHERE email_id = ?
        """,
        (email_id,),
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


def mark_email_processed(
    email_id: str,
    sender: str,
    subject: str,
    summary: str,
    importance: str,
    action_required: bool,
):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO emails (
            email_id,
            sender,
            subject,
            processed_at,
            summary,
            importance,
            action_required
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email_id,
            sender,
            subject,
            datetime.utcnow().isoformat(),
            summary,
            importance,
            int(action_required),
        ),
    )

    conn.commit()
    conn.close()


def get_todays_emails():
    """Return emails processed today."""

    conn = get_connection()

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            email_id,
            sender,
            subject,
            summary,
            importance,
            action_required,
            processed_at
        FROM emails
        WHERE date(processed_at) = date('now')
        ORDER BY processed_at DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def search_emails(
    query: str,
    limit: int = 10,
):
    """Search processed emails using individual query keywords.

    This is more tolerant of natural-language questions than matching
    the entire question as one LIKE pattern.
    """

    query = query.strip()

    if not query:
        return []

    # Ignore common question words so queries such as
    # "Where is the Generative AI Mastermind?" can match
    # "Generative AI Mastermind" in the stored email.
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "did",
        "do",
        "does",
        "for",
        "from",
        "get",
        "got",
        "have",
        "i",
        "in",
        "is",
        "me",
        "my",
        "of",
        "on",
        "the",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "email",
        "emails",
        "mail",
        "mails",
    }

    words = [
        word.strip(".,!?;:()[]{}\"'").lower()
        for word in query.split()
    ]

    keywords = [
        word
        for word in words
        if len(word) >= 2 and word not in stop_words
    ]

    if not keywords:
        keywords = words

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build a relevance score from keyword matches.
    score_parts = []
    where_parts = []
    params = []

    for keyword in keywords:
        pattern = f"%{keyword}%"

        score_parts.append(
            """
            CASE
                WHEN lower(subject) LIKE ? THEN 3
                WHEN lower(sender) LIKE ? THEN 3
                WHEN lower(summary) LIKE ? THEN 2
                ELSE 0
            END
            """
        )
        params.extend([pattern, pattern, pattern])

        where_parts.append(
            """
            (
                lower(subject) LIKE ?
                OR lower(sender) LIKE ?
                OR lower(summary) LIKE ?
            )
            """
        )
        params.extend([pattern, pattern, pattern])

    score_sql = " + ".join(score_parts)
    where_sql = " OR ".join(where_parts)

    cursor.execute(
        f"""
        SELECT
            email_id,
            sender,
            subject,
            summary,
            importance,
            action_required,
            processed_at,
            ({score_sql}) AS relevance_score
        FROM emails
        WHERE {where_sql}
        ORDER BY relevance_score DESC, processed_at DESC
        LIMIT ?
        """,
        (*params, limit),
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            key: row[key]
            for key in row.keys()
            if key != "relevance_score"
        }
        for row in rows
    ]

