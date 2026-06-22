from flask import request, jsonify, Flask, send_file
from processor import Processor
from database import DatabaseAdmin, db
from routes import admin_bp, auth_bp, student_bp, tutors_bp, chatbot_bp
from services.moodle_config_service import MoodleConfigError, require_saved_moodle_config
from dotenv import load_dotenv
from flask_cors import CORS
import atexit
import os

from auth import authenticate_request, init_auth

load_dotenv()


def _build_local_database_uri():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 5432))
    db_name = os.getenv("DB_DATABASE")

    return f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-me"),
    SECURITY_PASSWORD_SALT=os.getenv("SECURITY_PASSWORD_SALT", "dev-password-salt-change-me"),
    SECURITY_API_ENABLED_METHODS=["session"],
    WTF_CSRF_ENABLED=False,
    SECURITY_RETURN_GENERIC_RESPONSES=True,
    SECURITY_EMAIL_VALIDATOR_ARGS={"check_deliverability": False},
    SECURITY_TOKEN_AUTHENTICATION_HEADER=None,
    SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    REMEMBER_COOKIE_SAMESITE=os.getenv("REMEMBER_COOKIE_SAMESITE", "Lax"),
    REMEMBER_COOKIE_SECURE=os.getenv("REMEMBER_COOKIE_SECURE", "false").lower() == "true",
    REMEMBER_COOKIE_DURATION=int(os.getenv("REMEMBER_COOKIE_DURATION", 2592000)),
    SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI") or _build_local_database_uri(),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
)
CORS(app, supports_credentials=True)

atexit.register(DatabaseAdmin.dispose_connector)

db.init_app(app)
init_auth(app)

app.register_blueprint(student_bp)
app.register_blueprint(tutors_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chatbot_bp)
app.before_request(authenticate_request)


def run_scheduled_analysis(channel="diario"):
    """Daily job entrypoint used by the scheduler process."""
    try:
        db_inst_config = require_saved_moodle_config()
        processor = Processor(user=1)
        version = processor.get_version(institution_id=1, db_config=db_inst_config)
        processor.set_subjects_analysis(db_config=db_inst_config, channel=channel)
        print(f"[scheduler] {channel.capitalize()} analysis dispatch finished. version={version}")
    except MoodleConfigError as e:
        print(f"[scheduler] {channel.capitalize()} analysis dispatch skipped: {e.message}")
    except Exception as e:
        print(f"[scheduler] {channel.capitalize()} analysis dispatch failed: {e}")


@app.route("/analysis", methods=["PUT"])
def analysis():
    if request.method == "OPTIONS":
        return "", 200

    payload = request.get_json() or {}
    channel = payload.get("channel", "diario")
    print("channel:", channel)
    try:
        db_inst_config = require_saved_moodle_config()
    except MoodleConfigError as e:
        return jsonify({"error": e.message}), e.status_code

    processor = Processor(user=1)
    version = processor.get_version(institution_id=1, db_config=db_inst_config)
    processor.set_subjects_analysis(db_config=db_inst_config, channel=channel)

    result = {"message": "Análises iniciadas com sucesso", "version": version}
    return jsonify(result), 200


@app.route("/")
def hello():
    return send_file(
        "pages/app.html", mimetype="text/html", download_name="app.html"
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)
