import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "tasks.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    connection = db_connection()
    try:
        connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        connection.commit()
    finally:
        connection.close()


@app.get("/")
def index():
    return jsonify({
        "service": os.getenv("APP_NAME", "Cloud Tasks"),
        "status": "running"
    })


@app.get("/health")
def health():
    return jsonify({"status": "ok"})

#______________________________________________________________________________
# тут 4 задача
@app.get("/api/tasks")
def list_tasks():
    filter_value = request.args.get("done")

    query = "SELECT id, title, done, created_at FROM tasks"
    params = []

    if filter_value is not None:
        if filter_value.lower() == "true":
            query += " WHERE done = ?"
            params.append(1)
        elif filter_value.lower() == "false":
            query += " WHERE done = ?"
            params.append(0)
        else:
            return jsonify({"error": "Параметр done должен быть true или false"}), 400

    query += " ORDER BY id DESC"

    connection = db_connection()
    try:
        rows = connection.execute(query, params).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        connection.close()


@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Укажите название задачи"}), 400

    title = title.strip()
    if len(title) > 100:
        return jsonify({"error": "Слишком длинное название"}), 400

    connection = db_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO tasks (title) VALUES (?)", (title,)
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()
        return jsonify(dict(row)), 201
    finally:
        connection.close()

#______________________________________________________________________________
#задание 1::
@app.get("/api/tasks/<int:task_id>")
def get_task(task_id):
    connection = db_connection()
    try:
        row = connection.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if row is None:
            return jsonify({"error": "Задача не найдена"}), 404

        return jsonify(dict(row))
    finally:
        connection.close()

#______________________________________________________________________________
#задание 2
@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400

    if "done" not in data:
        return jsonify({"error": "Поле done обязательно"}), 400

    value = data["done"]
    if type(value) is not bool:
        return jsonify({"error": "Поле done должно быть true или false"}), 400

    connection = db_connection()
    try:
        cursor = connection.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (int(value), task_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Задача не найдена"}), 404

        row = connection.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (task_id,)).fetchone()
        return jsonify(dict(row))
    finally:
        connection.close()

#______________________________________________________________________________
#задание 3:
@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    connection = db_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Задача не найдена"}), 404

        return "", 204
    finally:
        connection.close()

#______________________________________________________________________________
#задача 5:::
@app.get("/api/stats")
def stats():
    connection = db_connection()
    try:
        row = connection.execute("""
            SELECT COUNT(*) AS total,COALESCE(SUM(CASE WHEN done = 1 THEN 1 ELSE 0 END), 0) AS completed
            FROM tasks""").fetchone()

        total = row["total"]
        completed = row["completed"]
        return jsonify({
            "total": total,
            "completed": completed,
            "pending": total - completed
        })
    finally:
        connection.close()


initialize_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)