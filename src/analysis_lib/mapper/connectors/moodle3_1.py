from flask import jsonify
from ..moodle import Moodle
import csv
import pandas as pd

class Moodle31(Moodle):
    def __init__(self, connector):
        super().__init__(connector)
    
    def save_foruns_ava_csv(self, subject_id):
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
            ''', (subject_id, ))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        with open("exports/foruns_ava.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows([list(r.values()) for r in rows])
    
    def save_all_student_csv(self, subject_id):
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
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        with open("exports/all_students.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows([list(r.values()) for r in rows])
    
    def get_courses(self):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('SELECT id AS subject_id, fullname FROM mdl_course')
            courses = cur.fetchall()
        return courses


    '''
    Consultas relacionadas ao indicador de Engajamento:
    '''

    def get_all_posts_for_forum_required_by_course(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT p.userid AS user_id, f.id AS forum_id_required, p.id AS post_id_required
                FROM mdl_forum_posts p
                JOIN mdl_user u ON u.id = p.userid                      
                JOIN mdl_forum_discussions d ON d.id = p.discussion
                JOIN mdl_forum f ON f.id = d.forum
                WHERE f.course = %s AND f.assessed <> 0
                    AND EXISTS (
                        SELECT 1
                        FROM mdl_role_assignments ra2
                        JOIN mdl_role r2 ON r2.id = ra2.roleid
                        JOIN mdl_context c2 ON c2.id = ra2.contextid
                        WHERE ra2.userid = p.userid
                            AND r2.id IN (5)            
                            AND c2.contextlevel = 50
                            AND c2.instanceid = f.course
                    )
                ORDER BY d.id, p.created;
            ''', (subject_id, ))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
        
    
    def get_all_students_by_course(self, subject_id):
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
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas ao indicador de Desempenho:
    '''

    def get_grades_by_course(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    u.id AS user_id,
                    u.firstname,
                    gi.courseid,
                    gg.finalgrade AS grade_final,
                    cm.id AS activity_id,
                    gi.itemname AS activity_name,
                    WEEK(FROM_UNIXTIME(cm.added)) AS week
                FROM mdl_user u
                JOIN mdl_grade_grades gg ON gg.userid = u.id
                JOIN mdl_grade_items gi ON gi.id = gg.itemid
                JOIN mdl_course_modules cm ON cm.instance = gi.iteminstance
                JOIN mdl_modules m ON m.id = cm.module AND m.name = gi.itemmodule
                WHERE gi.itemtype = 'mod'
                AND gi.courseid = %s
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_activity_weights(self, subject_id):
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
            ''', (subject_id, subject_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas ao indicador de Motivação:
    '''

    def get_foruns_non_required_by_course(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT p.userid AS user_id, f.id AS forum_id_unrequired, p.id AS post_id_unrequired
                FROM mdl_forum_posts p
                JOIN mdl_user u ON u.id = p.userid                      
                JOIN mdl_forum_discussions d ON d.id = p.discussion
                JOIN mdl_forum f ON f.id = d.forum
                WHERE f.course = %s AND f.assessed = 0
                    AND EXISTS (
                        SELECT 1
                        FROM mdl_role_assignments ra2
                        JOIN mdl_role r2 ON r2.id = ra2.roleid
                        JOIN mdl_context c2 ON c2.id = ra2.contextid
                        WHERE ra2.userid = p.userid
                            AND r2.id IN (5)            
                            AND c2.contextlevel = 50
                            AND c2.instanceid = f.course
                    )
                ORDER BY d.id, p.created;
            ''', (subject_id, ))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas ao indicador Pedagógico:
    '''

    def get_forum_data(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    t.tutor_id,
                    t.tutor_completo,
                    r.resposta_id,
                    r.discussion_id,
                    r.discussion_title,
                    r.forum_id,
                    r.forum_name,
                    r.autor_resposta_id,
                    r.autor_resposta_completo,
                    r.resposta_enviada_em,
                    r.post_aluno_id,
                    r.autor_aluno_completo,
                    r.post_criado_em,
                    r.aluno_id
                FROM
                    (
                    SELECT u.id AS tutor_id,
                            CONCAT_WS(' ', u.firstname, u.lastname) AS tutor_completo
                    FROM mdl_user u
                    JOIN mdl_role_assignments ra ON ra.userid = u.id
                    JOIN mdl_role r ON r.id = ra.roleid
                    JOIN mdl_context c ON c.id = ra.contextid
                    WHERE r.id IN (3,4,9,17)
                        AND c.contextlevel = 50
                        AND c.instanceid = %s
                    ) AS t
                LEFT JOIN
                    (
                    SELECT 
                        p.id AS resposta_id,
                        p.discussion AS discussion_id,
                        d.name AS discussion_title,
                        f.id AS forum_id,
                        f.name AS forum_name,
                        p.userid AS autor_resposta_id,
                        CONCAT_WS(' ', u.firstname, u.lastname) AS autor_resposta_completo,
                        FROM_UNIXTIME(p.created) AS resposta_enviada_em,
                        parent.id AS post_aluno_id,
                        parent.userid AS aluno_id,
                        CONCAT_WS(' ', u2.firstname, u2.lastname) AS autor_aluno_completo,
                        FROM_UNIXTIME(parent.created) AS post_criado_em
                    FROM mdl_forum_posts p
                    JOIN mdl_user u ON u.id = p.userid
                    JOIN mdl_forum_discussions d ON d.id = p.discussion
                    JOIN mdl_forum f ON f.id = d.forum
                    JOIN mdl_forum_posts parent ON parent.id = p.parent
                    JOIN mdl_user u2 ON u2.id = parent.userid
                    WHERE f.course = %s
                        AND EXISTS (
                            SELECT 1
                            FROM mdl_role_assignments ra
                            JOIN mdl_role r ON r.id = ra.roleid
                            JOIN mdl_context c ON c.id = ra.contextid
                            WHERE ra.userid = p.userid
                            AND r.id IN (3,4,9,17)
                            AND c.contextlevel = 50
                            AND c.instanceid = f.course
                        )
                        AND EXISTS (
                            SELECT 1
                            FROM mdl_role_assignments ra2
                            JOIN mdl_role r2 ON r2.id = ra2.roleid
                            JOIN mdl_context c2 ON c2.id = ra2.contextid
                            WHERE ra2.userid = parent.userid
                            AND r2.id IN (5)
                            AND c2.contextlevel = 50
                            AND c2.instanceid = f.course
                        )
                    ) AS r
                ON t.tutor_id = r.autor_resposta_id
                ORDER BY r.discussion_id, r.resposta_enviada_em;
            ''', (subject_id, subject_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas ao indicador de profundidade cognitiva::
    '''

    # Fóruns
    def get_course_forum_viewed(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.objectid AS forum_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_user u ON lh.userid = u.id
                WHERE lh.courseid = %s
                AND lh.eventname LIKE '%%course_module_viewed%%'
                AND lh.component = 'mod_forum';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_forum_post_created(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.objectid AS post_id,
                    p.discussion AS forum_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_forum_posts p ON lh.objectid = p.id
                JOIN mdl_user u ON lh.userid = u.id
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = lh.courseid
                WHERE lh.courseid = %s
                AND (lh.eventname LIKE '%%post_created%%'
                    OR lh.eventname LIKE '%%discussion_created%%')
                AND lh.component = 'mod_forum';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def forum_reply_viewed(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT 
                    p.userid AS user_id,
                    d.id AS discussion_id,
                    d.forum AS forum_id,
                    p.id AS original_post_id,
                    reply.id AS reply_post_id,
                    lh.timecreated AS timestamp
                FROM mdl_forum_posts p
                JOIN mdl_forum_discussions d ON p.discussion = d.id
                JOIN mdl_logstore_standard_log lh 
                    ON lh.objectid = d.id AND lh.userid = p.userid
                JOIN mdl_forum_posts reply 
                    ON reply.parent = p.id AND reply.userid <> p.userid
                WHERE p.parent = 0
                AND lh.courseid = %s
                AND lh.eventname LIKE '%%discussion_viewed%%'
                AND lh.timecreated >= reply.created  
                AND lh.userid <> reply.userid
                AND lh.component = 'mod_forum';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    # Assign
    def get_assign_submission_status_viewed(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.contextinstanceid AS assignment_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_user u ON lh.userid = u.id
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = lh.courseid
                WHERE lh.courseid = %s
                AND lh.eventname LIKE '%%submission_status_viewed%%'
                    AND lh.component = 'mod_assign';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_assign_assessable_submitted(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.contextinstanceid AS assignment_id,
                    lh.objectid AS submission_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_user u ON lh.userid = u.id
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = lh.courseid
                WHERE lh.courseid = %s
                AND lh.eventname LIKE '%%assessable_submitted%%'
                        AND lh.component = 'mod_assign';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_assign_feedback_viewed(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.contextinstanceid AS assignment_id,
                    lh.objectid AS submission_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_user u ON lh.userid = u.id
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = lh.courseid
                WHERE lh.courseid = %s
                AND lh.eventname LIKE '%%feedback_viewed%%'
                        AND lh.component = 'mod_assign';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    # Quizzes
    def get_quizz_viewed(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.contextinstanceid AS quiz_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_user u ON lh.userid = u.id
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = lh.courseid
                WHERE lh.courseid = %s
                AND lh.eventname LIKE '%%course_module_viewed%%'
                AND lh.component = 'mod_quiz';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_quizz_attempt_submitted(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.contextinstanceid AS quiz_id,
                    lh.objectid AS attempt_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_user u ON lh.userid = u.id
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = lh.courseid
                WHERE lh.courseid = %s
                AND lh.eventname LIKE '%%attempt_submitted%%'
                AND lh.component = 'mod_quiz';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_quizz_attempt_reviewd(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS user_id,
                    u.firstname,
                    lh.contextinstanceid AS quiz_id,
                    lh.objectid AS attempt_id,
                    lh.timecreated AS timestamp
                FROM mdl_logstore_standard_log lh
                JOIN mdl_user u ON lh.userid = u.id
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = lh.courseid
                WHERE lh.courseid = %s
                AND lh.eventname LIKE '%%attempt_reviewed%%'
                AND lh.component = 'mod_quiz';
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas as informações gerais das disciplinas para povoar as telas:
    '''
    def fetch_subject_info(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    c.id        AS subject_id,
                    c.fullname  AS name,
                    c.shortname AS abrev,
                    FROM_UNIXTIME(c.timecreated) AS date
                FROM mdl_course c
                WHERE c.id = %s;
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def fetch_subject_metrics(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            # 1) Total de alunos
            cur.execute('''
                SELECT COUNT(DISTINCT ra.userid) AS total_enrolled
                FROM mdl_role_assignments ra
                JOIN mdl_context ctx ON ctx.id = ra.contextid
                JOIN mdl_user u ON u.id = ra.userid
                JOIN mdl_role r ON r.id = ra.roleid AND r.id = 5
                WHERE ctx.contextlevel = 50 
                    AND ctx.instanceid = %s;

            ''', (subject_id,))
            total_rows = cur.fetchall()
            total_enrolled = total_rows[0]["total_enrolled"] if total_rows else 0

            # 2) Média de notas
            cur.execute('''
                SELECT ROUND(AVG(gg.finalgrade), 2) AS avg_grade_all
                FROM mdl_grade_grades gg
                JOIN mdl_grade_items gi ON gi.id = gg.itemid
                WHERE gi.itemtype = 'course'
                AND gi.courseid = %s;
            ''', (subject_id,))
            avg_rows = cur.fetchall()
            avg_grade_all = avg_rows[0]["avg_grade_all"] if avg_rows else None

            # 3) Taxa de aprovação
            cur.execute('''
                SELECT
                    ROUND(
                        100.0 * SUM(CASE WHEN gg.finalgrade IS NOT NULL AND gg.finalgrade >= 70 THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(students.userid), 0),
                        2
                    ) AS taxa_aprovacao
                FROM (
                    SELECT DISTINCT ue.userid
                    FROM mdl_enrol e
                    JOIN mdl_user_enrolments ue ON ue.enrolid = e.id
                    JOIN mdl_role_assignments ra ON ra.userid = ue.userid
                    JOIN mdl_role r ON r.id = ra.roleid
                    JOIN mdl_context ctx ON ctx.id = ra.contextid
                    WHERE e.courseid = %s
                    AND ctx.contextlevel = 50
                    AND r.archetype = 'student'
                ) students
                JOIN mdl_grade_items gi ON gi.courseid = %s AND gi.itemtype = 'course'
                LEFT JOIN mdl_grade_grades gg ON gg.itemid = gi.id AND gg.userid = students.userid;
            ''', (subject_id, subject_id))
            rate_rows = cur.fetchall()
            taxa_aprovacao = rate_rows[0]["taxa_aprovacao"] if rate_rows else None

        data = [{
            "total_enrolled": int(total_enrolled or 0),
            "avg_grade_all": float(avg_grade_all) if avg_grade_all is not None else None,
            "taxa_aprovacao": float(taxa_aprovacao) if taxa_aprovacao is not None else None,
        }]
        df = pd.DataFrame(data)
        return df
    
    def get_pct_usage_resource(self, subject_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    cm.course AS subject_id,
                    m.name    AS modulo,
                    COUNT(*)  AS qtd,
                    ROUND(100.0 * COUNT(*) / 
                    (
                        SELECT COUNT(*)
                        FROM mdl_course_modules cm2
                        JOIN mdl_context ctx2
                            ON ctx2.contextlevel = 50
                        AND ctx2.instanceid   = cm2.course
                        WHERE cm2.course = cm.course
                        ),
                        2
                    ) AS pct_modulo_no_curso
                FROM mdl_course_modules cm
                JOIN mdl_modules m  ON m.id  = cm.module
                JOIN mdl_context ctx ON ctx.contextlevel = 50 AND ctx.instanceid = cm.course
                WHERE cm.course = %s
                GROUP BY cm.course, m.name
                ORDER BY pct_modulo_no_curso DESC, m.name;
            ''', (subject_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_all_subjects(self):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    c.id                           AS id,
                    c.fullname                     AS fullname,
                    c.shortname                    AS shortname,
                    c.startdate                    AS startdate
                FROM mdl_course c
                WHERE c.id <> 1;
            ''', ())
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
        Página de aluno na disciplina
    '''

    def fetch_student_summary(self, subject_id, student_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT
                    u.id AS id,
                    CONCAT(u.firstname, ' ', u.lastname) AS name,
                    u.email AS email,
                    u.city, 
                    FROM_UNIXTIME(u.firstaccess) AS first_access_moodle,
                    FROM_UNIXTIME(ula.timeaccess) AS last_access_subject,
                    GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') AS student_groups,
                    cc2.name AS degree_program
                FROM mdl_user u
                JOIN mdl_user_enrolments ue ON ue.userid = u.id
                JOIN mdl_enrol e ON e.id = ue.enrolid
                JOIN mdl_role r ON r.id = e.roleid
                LEFT JOIN mdl_user_lastaccess ula ON ula.userid = u.id AND ula.courseid = e.courseid 
                JOIN mdl_groups_members gm ON gm.userid = u.id
                JOIN mdl_groups g ON g.id = gm.groupid AND g.courseid = e.courseid
                JOIN mdl_course c            ON c.id = e.courseid
                JOIN mdl_course_categories cc3 ON cc3.id = c.category
                JOIN mdl_course_categories cc2 ON cc2.id = cc3.parent
                WHERE e.courseid = %s AND u.id = %s AND r.archetype = 'student';
            ''', (subject_id, student_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def fetch_student_grades(self, subject_id, student_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    u.id AS id,
                    CONCAT(u.firstname, ' ', u.lastname) AS name,
                    gi.itemname AS activity_name,
                    gi.itemtype AS item_type,
                    gi.grademax AS grade_max,
                    g.finalgrade AS grade_real
                FROM mdl_user u
                JOIN mdl_grade_grades g ON g.userid = u.id
                JOIN mdl_grade_items gi ON gi.id = g.itemid
                JOIN mdl_course c ON c.id = gi.courseid
                JOIN mdl_course_categories cc ON cc.id = c.category
                WHERE gi.courseid = %s AND g.userid = %s;
            ''', (subject_id, student_id))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df