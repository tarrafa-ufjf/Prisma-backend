from flask import request, jsonify, Flask
from flask_mysql_connector import MySql
from dotenv import load_dotenv
from database import db
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = "tarrafa_flask_back_2014"
app.config['SQLALCHEMY_DATABASE_URI']  = os.getenv('MYSQL_ACCESS')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route("/course/<int:course_id>", methods=["GET"])
def get_course(course_id):
    return jsonify({}), 200

@app.route("/")
def hello():
    return "Hello, Flask + Poetry!"

if __name__ == '__main__':
    app.run(debug=True)