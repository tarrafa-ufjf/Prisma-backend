from flask import request, jsonify, Flask
# from flask_mysql_connector import MySql
from dotenv import load_dotenv
import pymysql
from database import db
import os

load_dotenv()

app = Flask(__name__)


def get_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_GRAD_PORT')),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DATABASE'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/courses')
def get_courses():
    connector = get_connection()
    with connector.cursor() as cursor:
        cursor.execute('''
            SELECT *
            FROM mdl_course
        ''')
        coursers = cursor.fetchall()
    connector.close()
    return jsonify(coursers), 200

@app.route('/course/<int:course_id>')
def get_course(course_id):
    connector = get_connection()
    with connector.cursor() as cursor:
        cursor.execute('''
            SELECT DISTINCT 
                u.id AS user_id,
                u.firstname,
                lh.objectid AS forum_id,
                FROM_UNIXTIME(lh.timecreated) AS timestamp
            FROM mdl_logstore_standard_log lh
            JOIN mdl_user u ON lh.userid = u.id
            JOIN mdl_user_enrolments ue ON ue.userid = u.id
            JOIN mdl_enrol e ON e.id = ue.enrolid
            JOIN mdl_role r ON r.id = e.roleid
            WHERE lh.courseid = %s
            AND lh.eventname LIKE '%%course_module_viewed%%'
            AND lh.component = 'mod_forum'
            AND r.archetype = 'student';
        ''', course_id)
        coursers = cursor.fetchall()
    connector.close()
    return jsonify(coursers), 200





@app.route("/")
def hello():
    return "Hello, Flask + Poetry!"

if __name__ == '__main__':
    app.run(debug=True)