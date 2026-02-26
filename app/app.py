from flask import Flask, request, jsonify
import sqlite3
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from config import Config


app = Flask(__name__)

app.config.from_object(Config)

DATABASE = Config.DATABASE
HOST = Config.HOST
PORT = Config.PORT

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

@app.route('/debug-config')
def debug_config():
    return {
        "database": app.config.get("DATABASE"),
        "host": app.config.get("HOST"),
        "port": app.config.get("PORT")
    }
  
if __name__ == "__main__":
    init_db()
    # app.run(host=HOST, port=PORT)
    print(f"--- CONFIG TEST ---")
    print(f"Database Path: {Config.DATABASE}")
    print(f"Host: {Config.HOST}")
    print(f"Port: {Config.PORT}")
    print(f"-------------------")
    app.run(host=Config.HOST, port=Config.PORT)