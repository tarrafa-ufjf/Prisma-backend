from flask import request, jsonify, Flask
from database import db, Database
import pandas as pd
from analysis.analysis import Analyzer

app = Flask(__name__)
conn = Database()
analyzer = Analyzer()

@app.route('/courses')
def get_courses():
    connector = conn.get_connection()
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
    connector = conn.get_connection()
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
        
        courses = cursor.fetchall()
        df = pd.DataFrame(courses)
        
        if not df.empty:
            df.rename(columns={'timestamp': 'timestamp'}, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        print(df)
        
    connector.close()
    
    # Return DataFrame as JSON if you want the converted data
    return jsonify(df.to_dict(orient='records')), 200


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

@app.route("/version", methods=["GET", "POST"])
def version():
    port = request.form.get('port', type=int)
    config = {
            'host':     request.form['host'],
            'port':     port,
            'db': request.form['database'],
            'user':     request.form['user'],
            'password': request.form['password'],
        }
    connector = conn.get_connection_with_config(config)

    version = analyzer.get_moodle_version(connector)
    page = f'''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta charset="UTF-8">
        <title>Versão do moodle</title>
        </head>
        <body>
            <p>A versão utilizada do moodle é a: {version}</p>
        </body>
        </html>
    '''
    return page, 200


@app.route("/")
def hello():
    page = '''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta charset="UTF-8">
        <title>Configuração de Banco Moodle</title>
        </head>
        <body>
        <h2>Configuração de Conexão ao Banco de Dados Moodle</h2>
        <form method="post" action="/version">
            <div>
            <label for="host">Host (ex: localhost):</label>
            <input id="host" name="host" type="text" required>
            </div>
            <div>
            <label for="port">Port:</label>
            <input id="port" name="port" type="text" required>
            </div>
            <div>
            <label for="database">Nome do Banco:</label>
            <input id="database" name="database" type="text" required>
            </div>
            <div>
            <label for="user">Usuário:</label>
            <input id="user" name="user" type="text" required>
            </div>
            <div>
            <label for="password">Senha:</label>
            <input id="password" name="password" type="password">
            </div>
            <div>
            <button type="submit">Salvar Configuração</button>
            </div>
        </form>
        </body>
        </html>

    '''
    return page

if __name__ == '__main__':
    app.run(debug=True)