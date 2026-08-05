from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "et617-learning-app-secret"
DB_PATH = Path(__file__).with_name("learning_app.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'learner'
        );

        CREATE TABLE IF NOT EXISTS clickstream (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_target TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )

    existing = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if existing == 0:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("learner", "demo123", "learner"),
        )
    conn.commit()
    conn.close()


def log_event(user_id: int, event_type: str, event_target: str = "", metadata: dict | None = None) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO clickstream (user_id, event_type, event_target, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            event_type,
            event_target,
            json.dumps(metadata or {}, ensure_ascii=False),
            datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_connection()
        user = conn.execute(
            "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        conn.close()

        if user is None:
            return render_template("login.html", error="Invalid learner credentials.")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        log_event(user["id"], "login", "portal")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return render_template("login.html", error="Username and password are required.")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, "learner"),
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return render_template("login.html", error="That learner name already exists.")
    conn.close()

    session["user_id"] = user_id
    session["username"] = username
    session["role"] = "learner"
    log_event(user_id, "register", "portal")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    if "user_id" in session:
        log_event(session["user_id"], "logout", "portal")
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    log_event(user_id, "page_view", "dashboard")

    conn = get_connection()
    row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    recent = conn.execute(
        """
        SELECT event_type, event_target, metadata, created_at
        FROM clickstream
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,),
    ).fetchall()
    total_events = conn.execute("SELECT COUNT(*) AS count FROM clickstream WHERE user_id = ?", (user_id,)).fetchone()["count"]
    conn.close()

    return render_template(
        "dashboard.html",
        username=row["username"],
        recent_activity=recent,
        total_events=total_events,
    )


@app.route("/api/log_event", methods=["POST"])
def api_log_event():
    if "user_id" not in session:
        return jsonify({"ok": False, "message": "Not authenticated"}), 401

    payload = request.get_json(silent=True) or {}
    event_type = payload.get("event_type", "click")
    event_target = payload.get("event_target", "")
    metadata = payload.get("metadata") or {}
    log_event(session["user_id"], event_type, event_target, metadata)
    return jsonify({"ok": True})


@app.route("/api/activity")
def api_activity():
    if "user_id" not in session:
        return jsonify({"ok": False, "message": "Not authenticated"}), 401

    conn = get_connection()
    row = conn.execute(
        """
        SELECT event_type, COUNT(*) AS count
        FROM clickstream
        WHERE user_id = ?
        GROUP BY event_type
        ORDER BY count DESC
        """,
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return jsonify({"ok": True, "events": [dict(r) for r in row]})


init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
