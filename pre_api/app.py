from flask import request, jsonify, Flask, send_file
from processor import Processor
from routes.student_routes import student_bp
from routes.tutors_routes import tutors_bp
# from flasgger import Swagger
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# swagger = Swagger(app)
load_dotenv()

app.register_blueprint(student_bp)
app.register_blueprint(tutors_bp)

@app.route("/analysis", methods=["PUT"])
def analysis():
    if request.method == "OPTIONS":
        return "", 200
    
    # global indicators
    db_inst_config = request.get_json()
    processor = Processor(user=1)
    version = processor.get_version(institution_id=1, db_config=db_inst_config)

    try:
        processor.db_admin.insert_version_in_database(1, version, db_inst_config)
    except Exception as e:
        print(f"Erro ao inserir versão na base de dados: {e}")

    processor.set_subjects_analysis(db_config=db_inst_config)

    result = {"message": "Análises iniciadas com sucesso",
              "version": version}
    return jsonify(result), 200

@app.route("/")
def hello():
    return send_file('pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True)