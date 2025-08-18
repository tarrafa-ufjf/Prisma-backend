from flask import request, jsonify, Flask, send_file, send_from_directory
from database import db, Database
import pandas as pd
from analysis.analysis import Analyzer

app = Flask(__name__)
conn = Database()
analyzer = Analyzer()
connector = None
version = None

@app.route("/versions", methods=["GET"])
def moodle_version():
    connector = conn.get_connection()
    with connector.cursor() as cursor:
        cursor.execute('''
            SELECT *
            FROM mdl_course
        ''')
        coursers = cursor.fetchall()
    connector.close()
    return jsonify(coursers), 200

@app.route("/engagement", methods=["GET"])
def engagement():
    print(request.args)
    course_id = request.args.get('engagement-id', type=int)
    if not course_id:
        return jsonify({"error": "Course ID is required"}), 400
    
    res = analyzer.engagement_analysis(course_id, request.args.get('engagement-query'), version, connector)

    return jsonify(res.to_dict(orient="records")), 200

@app.route("/analysis", methods=["GET"])
def analysis():
    global connector, version
    port = request.args.get('port', type=int)
    config = {
            'host':     request.args['host'],
            'port':     port,
            'db':       request.args['database'],
            'user':     request.args['user'],
            'password': request.args['password'],
        }
    connector = conn.get_connection_with_config(config)

    version = analyzer.get_moodle_version(connector)

    res = analyzer.general_query(connector, version)

    return send_from_directory('src/pages', 'analysis.html'), 200


@app.route("/")
def hello():
    return send_file('src/pages/app.html',
        mimetype='text/html',
        download_name='app.html'), 200

if __name__ == '__main__':
    app.run(debug=True)