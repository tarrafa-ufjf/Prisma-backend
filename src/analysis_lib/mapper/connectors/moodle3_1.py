from flask import jsonify
from ..moodle import Moodle
import csv
import pandas as pd

class Moodle31(Moodle):
    def __init__(self, connector):
        super().__init__(connector)
    
    def save_foruns_ava_csv(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT p.userid AS user_id, f.id AS forum_id_required, p.id AS post_id_required, p.created AS post_date_required
                FROM mdl_forum f
                JOIN mdl_forum_discussions d ON d.forum = f.id 
                JOIN mdl_forum_posts p ON p.discussion = d.id
                JOIN mdl_user u ON u.id = p.userid
                JOIN mdl_role_assignments ra ON ra.userid = u.id
                JOIN mdl_context ctxt ON ctxt.id = ra.contextid
                WHERE f.course = %s AND 
                    ra.roleid = 5 AND 
                    ctxt.contextlevel = 50 AND 
                    ctxt.instanceid = f.course AND 
                    f.assessed <> 0;
            ''', (course_id, ))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        with open("exports/foruns_ava.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows([list(r.values()) for r in rows])
    
    def save_all_student_csv(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT u.id AS user_id
                FROM mdl_user u
                JOIN mdl_user_enrolments ue ON ue.userid = u.id
                JOIN mdl_enrol e ON e.id = ue.enrolid
                JOIN mdl_role r ON r.id = e.roleid
                WHERE e.courseid = %s
                AND r.archetype = 'student'
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        with open("exports/all_students.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows([list(r.values()) for r in rows])
    
    def get_courses(self):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('SELECT id AS course_id, fullname FROM mdl_course')
            courses = cur.fetchall()
        return courses


    '''
    Consultas relacionadas ao indicador de Engajamento:
    '''

    def get_all_posts_for_forum_required_by_course(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT p.userid AS user_id, f.id AS forum_id_required, p.id AS post_id_required, p.created AS post_date_required
                FROM mdl_forum f
                JOIN mdl_forum_discussions d ON d.forum = f.id 
                JOIN mdl_forum_posts p ON p.discussion = d.id
                JOIN mdl_user u ON u.id = p.userid
                JOIN mdl_role_assignments ra ON ra.userid = u.id
                JOIN mdl_context ctxt ON ctxt.id = ra.contextid
                WHERE f.course = %s AND 
                    ra.roleid = 5 AND 
                    ctxt.contextlevel = 50 AND 
                    ctxt.instanceid = f.course AND 
                    f.assessed <> 0;
            ''', (course_id, ))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
        
    
    def get_all_students_by_course(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT u.id AS user_id, CONCAT(u.firstname, ' ', u.lastname) AS full_name
                FROM mdl_user u
                JOIN mdl_user_enrolments ue ON ue.userid = u.id
                JOIN mdl_enrol e ON e.id = ue.enrolid
                JOIN mdl_role r ON r.id = e.roleid
                WHERE e.courseid = %s
                AND r.archetype = 'student'
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas ao indicador de Desempenho:
    '''

    def get_grades_by_course(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    u.id AS user_id,
                    u.firstname,
                    gi.courseid,
                    cm.id AS activity_id,
                    gi.itemname AS activity_name,
                    WEEK(FROM_UNIXTIME(cm.added)) AS week,
                    ((COALESCE(gg.finalgrade, 0) / gi.grademax)*100) AS performance
                FROM mdl_user u
                JOIN mdl_grade_grades gg ON gg.userid = u.id
                JOIN mdl_grade_items gi ON gi.id = gg.itemid
                JOIN mdl_course_modules cm ON cm.instance = gi.iteminstance
                JOIN mdl_modules m ON m.id = cm.module AND m.name = gi.itemmodule
                WHERE gi.itemtype = 'mod'
                AND gi.courseid = %s
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_activity_weights(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    cm.id AS activity_id,
                    gi.itemname AS activity_name,
                    gi.grademax,
                    ROUND((gi.grademax / total_course.total_max) * 100, 2) AS peso_percentual
                FROM mdl_grade_items gi
                JOIN mdl_modules m ON m.name = gi.itemmodule
                JOIN mdl_course_modules cm 
                    ON cm.instance = gi.iteminstance AND cm.module = m.id AND cm.course = gi.courseid
                JOIN (
                    SELECT grademax AS total_max
                    FROM mdl_grade_items
                    WHERE itemtype = 'course' AND courseid = %s
                    LIMIT 1
                ) AS total_course ON 1=1
                WHERE gi.courseid = %s
                AND gi.itemtype = 'mod';
            ''', (course_id, course_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas ao indicador de Motivação:
    '''

    def get_foruns_non_required_by_course(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT p.userid AS user_id, f.id AS forum_id_unrequired, p.id AS post_id_unrequired
                FROM mdl_forum f
                JOIN mdl_forum_discussions d ON d.forum = f.id 
                JOIN mdl_forum_posts p ON p.discussion = d.id
                JOIN mdl_user u ON u.id = p.userid
                JOIN mdl_role_assignments ra ON ra.userid = u.id
                JOIN mdl_context ctxt ON ctxt.id = ra.contextid
                WHERE f.course = %s AND 
                    ra.roleid = 5 AND 
                    ctxt.contextlevel = 50 AND 
                    ctxt.instanceid = f.course AND 
                    f.assessed = 0;
            ''', (course_id, ))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas ao indicador Pedagógico:
    '''

    def get_forum_data(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    f.id AS forum_id,
                    f.name AS forum_name,
                    p.id AS post_aluno_id,
                    p.userid AS aluno_id,
                    CONCAT_WS(' ', ua.firstname, ua.lastname) AS aluno_completo,
                    rp.id AS resposta_id,
                    rp.userid AS autor_resposta_id,
                    CONCAT_WS(' ', urp.firstname, urp.lastname) AS autor_resposta_completo,
                    rp.message AS resposta,
                    FROM_UNIXTIME(rp.created) AS resposta_enviada_em,
                    FROM_UNIXTIME(p.created) AS post_criado_em
                FROM mdl_forum_posts p
                JOIN mdl_forum_discussions d 
                    ON p.discussion = d.id
                JOIN mdl_forum f 
                    ON d.forum = f.id
                JOIN mdl_user ua 
                    ON ua.id = p.userid
                LEFT JOIN mdl_forum_posts rp 
                    ON rp.parent = p.id
                LEFT JOIN mdl_user urp 
                    ON urp.id = rp.userid
                -- 🔹 Subquery que define quem é considerado professor/tutor no curso
                LEFT JOIN (
                    SELECT u.id AS userid, r.shortname AS papel
                    FROM mdl_user u
                    JOIN mdl_role_assignments ra ON ra.userid = u.id
                    JOIN mdl_role r ON r.id = ra.roleid
                    JOIN mdl_context ctx ON ctx.id = ra.contextid
                    WHERE ctx.contextlevel = 50
                    AND ctx.instanceid = %s
                    AND r.id IN (3, 4, 9, 17)
                ) profs ON profs.userid = rp.userid
                -- 🔹 Papel do aluno continua sendo checado
                LEFT JOIN mdl_role_assignments ra_aluno 
                    ON ra_aluno.userid = p.userid
                LEFT JOIN mdl_role r_aluno 
                    ON r_aluno.id = ra_aluno.roleid
                LEFT JOIN mdl_context ctx_aluno 
                    ON ctx_aluno.id = ra_aluno.contextid
                AND ctx_aluno.contextlevel = 50
                AND ctx_aluno.instanceid = f.course
                WHERE f.course = %s
                AND p.parent = 0
                AND r_aluno.shortname = 'estudante'
                -- 🔹 agora o filtro de resposta considera só quem está na subquery "profs"
                AND (profs.userid IS NOT NULL OR rp.id IS NULL) 
                ORDER BY p.id, rp.created;
            ''', (course_id, course_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_private_messages(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    m.id AS mensagem_id,
                    m.useridfrom AS remetente_id,
                    CONCAT_WS(' ', uf.firstname, uf.lastname) AS remetente_completo,
                    m.useridto AS destinatario_id,
                    CONCAT_WS(' ', ut.firstname, ut.lastname) AS destinatario_completo,
                    m.fullmessage AS mensagem,
                    FROM_UNIXTIME(m.timecreated) AS enviada_em
                FROM mdl_message m
                JOIN mdl_user uf ON uf.id = m.useridfrom
                JOIN mdl_user ut ON ut.id = m.useridto
                -- 🔹 Subquery para identificar os professores/tutores do curso
                JOIN (
                    SELECT u.id AS userid
                    FROM mdl_user u
                    JOIN mdl_role_assignments ra ON ra.userid = u.id
                    JOIN mdl_role r ON r.id = ra.roleid
                    JOIN mdl_context ctx ON ctx.id = ra.contextid
                    WHERE ctx.contextlevel = 50
                    AND ctx.instanceid = %s
                    AND r.id IN (3, 4, 9, 17)
                ) profs ON profs.userid = m.useridfrom
                -- 🔹 Subquery para identificar os estudantes do curso
                JOIN (
                    SELECT u.id AS userid
                    FROM mdl_user u
                    JOIN mdl_role_assignments ra ON ra.userid = u.id
                    JOIN mdl_role r ON r.id = ra.roleid
                    JOIN mdl_context ctx ON ctx.id = ra.contextid
                    WHERE ctx.contextlevel = 50
                    AND ctx.instanceid = %s
                    AND r.shortname = 'estudante'
                ) alunos ON alunos.userid = m.useridto
                ORDER BY m.id;
            ''', (course_id, course_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_tutor_access_frequency(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    l.userid AS tutor_id,
                    CONCAT_WS(' ', u.firstname, u.lastname) AS tutor_completo,
                    COUNT(*) AS total_events,
                    COUNT(DISTINCT FROM_UNIXTIME(l.timecreated, '%%Y-%%m-%%d')) AS dias_acesso,
                    FROM_UNIXTIME(MAX(l.timecreated)) AS ultimo_acesso
                FROM mdl_logstore_standard_log l
                JOIN mdl_user u 
                    ON u.id = l.userid
                -- 🔹 Subquery de professores/tutores no curso
                JOIN (
                    SELECT u.id AS userid
                    FROM mdl_user u
                    JOIN mdl_role_assignments ra ON ra.userid = u.id
                    JOIN mdl_role r ON r.id = ra.roleid
                    JOIN mdl_context ctx ON ctx.id = ra.contextid
                    WHERE ctx.contextlevel = 50
                    AND ctx.instanceid = %s
                    AND r.id IN (3, 4, 9, 17)
                ) profs ON profs.userid = l.userid
                WHERE l.courseid = %s
                GROUP BY l.userid;
            ''', (course_id, course_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df