
import os
import re

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database configuration
database_url = os.getenv("DATABASE_URL", "sqlite:///portfolio.db")

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Allow requests from your deployed frontend
frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                origin.strip()
                for origin in frontend_url.split(",")
            ]
        }
    },
)


# Database model
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)


# Health check endpoint
@app.get("/")
def home():
    return jsonify({
        "message": "Navin Portfolio API is running"
    })


# Contact form endpoint
@app.post("/api/contact")
def submit_contact():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request"}), 400

    name = data.get("name", "")
    email = data.get("email", "")
    subject = data.get("subject", "")
    message = data.get("message", "")

    # Validate input types
    if not all(
        isinstance(value, str)
        for value in [name, email, subject, message]
    ):
        return jsonify({"error": "Invalid form data"}), 400

    # Remove extra whitespace
    name = name.strip()
    email = email.strip()
    subject = subject.strip()
    message = message.strip()

    # Validate required fields
    if not all([name, email, subject, message]):
        return jsonify({
            "error": "All fields are required"
        }), 400

    if (
        len(name) > 100
        or len(email) > 254
        or len(subject) > 200
        or len(message) > 5000
    ):
        return jsonify({
            "error": "One or more fields are too long"
        }), 400

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({
            "error": "Enter a valid email address"
        }), 400

    try:
        contact = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
        )

        db.session.add(contact)
        db.session.commit()

        return jsonify({
            "message": "Your message was sent successfully!"
        }), 201

    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to save contact message")

        return jsonify({
            "error": "Unable to save your message. Please try again."
        }), 500


# Create tables for this starter project
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
