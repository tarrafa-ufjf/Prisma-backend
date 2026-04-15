from flask import request, jsonify, Flask, send_file
from processor import Processor
from database import DatabaseAdmin
from routes import student_bp, tutors_bp
from dotenv import load_dotenv
from flask_cors import CORS
import atexit
import os

app = Flask(__name__)
CORS(app)
load_dotenv()

atexit.register(DatabaseAdmin.dispose_connector)

app.register_blueprint(student_bp)
app.register_blueprint(tutors_bp)


def _build_db_inst_config_from_env():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_GRAD_PORT")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


def run_scheduled_analysis(channel="diario"):
    """Daily job entrypoint used by the scheduler process."""
    db_inst_config = _build_db_inst_config_from_env()
    missing = [k for k, v in db_inst_config.items() if v in (None, "")]
    if missing:
        print(
            "[scheduler] Missing required environment variables for db_inst_config: "
            f"{', '.join(missing)}"
        )
        return

    try:
        processor = Processor(user=1)
        version = processor.get_version(institution_id=1, db_config=db_inst_config)

        try:
            processor.db_admin.insert_version_in_database(1, version, db_inst_config)
        except Exception as e:
            print(f"[scheduler] Erro ao inserir versão na base de dados: {e}")

        processor.set_subjects_analysis(db_config=db_inst_config, channel=channel)
        print(f"[scheduler] {channel.capitalize()} analysis dispatch finished. version={version}")
    except Exception as e:
        print(f"[scheduler] {channel.capitalize()} analysis dispatch failed: {e}")


@app.route("/analysis", methods=["PUT"])
def analysis():
    if request.method == "OPTIONS":
        return "", 200

    payload = request.get_json() or {}
    channel = payload.pop("channel", "diario")
    print("channel:", channel)
    db_inst_config = payload
    processor = Processor(user=1)
    version = processor.get_version(institution_id=1, db_config=db_inst_config)

    try:
        processor.db_admin.insert_version_in_database(1, version, db_inst_config)
    except Exception as e:
        print(f"Erro ao inserir versão na base de dados: {e}")

    processor.set_subjects_analysis(db_config=db_inst_config, channel=channel)

    result = {"message": "Análises iniciadas com sucesso", "version": version}
    return jsonify(result), 200


@app.route("/")
def hello():
    return send_file(
        "pages/app.html", mimetype="text/html", download_name="app.html"
    ), 200


if __name__ == "__main__":
    app.run(debug=True)
