import os
from flask import Flask, request, jsonify
import sqlite3
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


load_dotenv()

DATABASE = os.getenv("DATABASE", "database.db")
HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", 5000))

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    "app.log",
    maxBytes=1000000,   # 1MB per file
    backupCount=3       # keep 3 old log files
)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


@app.route("/health", methods=["GET"])
def health():
    logger.info("Health check endpoint accessed")
    return jsonify({"status": "healthy"}), 200


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data:
        logger.warning("Invalid input data: %s", data)
        return jsonify({"error": "Invalid input data"}), 400
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)",
            (data['name'], data['email'], datetime.now(timezone.utc)))
        conn.commit()
        conn.close()

        logger.info("User created: %s", data['email'])
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        logger.error("Error creating user: %s", e)
        return jsonify({"error": "Internal server error"}), 500
    

@app.route("/users", methods=["GET"])
def get_users():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, created_at FROM users")
        users = cursor.fetchall()
        conn.close()

        user_list = [{"id": user[0], "name": user[1], "email": user[2], "created_at": user[3]} for user in users]
        logger.info("Fetched %d users", len(user_list))
        return jsonify(user_list), 200
    except Exception as e:
        logger.error("Error fetching users: %s", e)
        return jsonify({"error": "Internal server error"}), 500

  
if __name__ == "__main__":
    init_db()
    app.run(host=HOST, port=PORT)