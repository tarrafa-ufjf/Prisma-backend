from flask import jsonify
from ..moodle import Moodle
import csv
import pandas as pd

class Moodle31(Moodle):
    def __init__(self, connector):
        super().__init__(connector)

    def save_foruns_ava_csv(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def save_all_student_csv(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_courses(self, connector):
        with connector.cursor() as cur:
            cur.execute('SELECT id AS subject_id, fullname FROM mdl_course')
            courses = cur.fetchall()
        return courses


    '''
    Consultas relacionadas ao indicador de Engajamento:
    '''

    def get_all_posts_for_forum_required_by_course(self, connector, subject_id):
        with connector.cursor() as cur:
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
        
    
    def get_all_students_by_course(self, connector, subject_id):
        with connector.cursor() as cur:
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

    def get_grades_by_course(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_activity_weights(self, connector, subject_id):
        with connector.cursor() as cur:
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

    def get_foruns_non_required_by_course(self, connector, subject_id):
        with connector.cursor() as cur:
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

    def get_forum_data(self, connector, subject_id):
        with connector.cursor() as cur:
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
    def get_course_forum_viewed(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_forum_post_created(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def forum_reply_viewed(self, connector, subject_id):
        with connector.cursor() as cur:
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
    def get_assign_submission_status_viewed(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_assign_assessable_submitted(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_assign_feedback_viewed(self, connector, subject_id):
        with connector.cursor() as cur:
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
    def get_quizz_viewed(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_quizz_attempt_submitted(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_quizz_attempt_reviewd(self, connector, subject_id):
        with connector.cursor() as cur:
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
    def fetch_subject_info(self, connector, subject_id):
        conn = self.connector
        with connector.cursor() as cur:
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
    
    def fetch_subject_metrics(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_pct_usage_resource(self, connector, subject_id):
        with connector.cursor() as cur:
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
    
    def get_all_subjects(self, connector):
        with connector.cursor() as cur:
            cur.execute('''
                SELECT
                    c.id        AS id,
                    c.fullname  AS fullname,
                    c.shortname AS shortname,
                    c.startdate AS startdate
                FROM mdl_course c
                JOIN mdl_context ctx ON ctx.instanceid = c.id
                AND ctx.contextlevel = 50
                JOIN mdl_role_assignments ra ON ra.contextid = ctx.id
                JOIN mdl_role r ON r.id = ra.roleid AND r.id = 5
                JOIN mdl_user u ON u.id = ra.userid
                WHERE c.id <> 1
                GROUP BY c.id, c.fullname, c.shortname, c.startdate
                HAVING COUNT(u.id) >= 10;
            ''', ())
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
        Página de aluno na disciplina
    '''

    def fetch_student_summary(self, connector, subject_id, student_id):
        with connector.cursor() as cur:
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
    
    def fetch_student_grades(self, connector, subject_id, student_id):
        with connector.cursor() as cur:
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
    
    '''
    Página de Home
    '''
    
    def fetch_subjects_summary(self, connector):
        with connector.cursor() as cur:
            cur.execute("""
                SELECT
                    c.id        AS subject_id,
                    c.fullname  AS name,
                    c.shortname AS abrev,
                    FROM_UNIXTIME(c.timecreated) AS date,
                    GROUP_CONCAT(
                        DISTINCT CASE
                            WHEN r.id = 3 THEN CONCAT(u.firstname, ' ', u.lastname)
                            ELSE NULL
                        END
                        ORDER BY u.firstname, u.lastname SEPARATOR ', '
                    ) AS teachers,
                    COUNT(
                        DISTINCT CASE
                            WHEN r.id = 5 THEN u.id
                            ELSE NULL
                        END
                    ) AS total_enrolled
                FROM mdl_course c
                LEFT JOIN mdl_context ctx ON ctx.instanceid = c.id AND ctx.contextlevel = 50
                LEFT JOIN mdl_role_assignments ra ON ra.contextid = ctx.id
                LEFT JOIN mdl_role r ON r.id = ra.roleid
                LEFT JOIN mdl_user u ON u.id = ra.userid
                GROUP BY c.id, c.fullname, c.shortname, c.timecreated;
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def fetch_institution_info(self, connector):
        with connector.cursor() as cur:
            cur.execute("""
                SELECT
                    (SELECT COUNT(*)
                    FROM mdl_user
                    WHERE deleted = 0) AS total_users,

                    (SELECT COUNT(id) AS total_degree_programs
                    FROM mdl_course_categories
                    WHERE depth = 2 AND parent IN (1, 20, 63, 233, 315)) AS total_courses_offered,

                    (SELECT DISTINCT COUNT(c.id) AS total_subjects
                    FROM mdl_course_categories cc1
                    JOIN mdl_course_categories cc2 ON cc2.parent = cc1.id
                    JOIN mdl_course_categories cc3 ON cc3.parent = cc2.id
                    JOIN mdl_course c ON c.category = cc3.id
                    WHERE cc2.depth = 2 AND cc2.parent IN (1, 20, 63, 233, 315)) AS total_subjects
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        df = pd.DataFrame(rows, columns=cols)
        return df   
    
    def fetch_responses_forums(self, connector, subject_id, start_at, end_at, tutor_ids):
        tutor_ids = [int(x) for x in tutor_ids if x is not None]
        if not tutor_ids:
            return pd.DataFrame(columns=[
                "tutor_id","tutor_completo","resposta_id","discussion_id","discussion_title",
                "forum_id","forum_name","autor_resposta_id","autor_resposta_completo",
                "resposta_enviada_em","post_aluno_id","autor_aluno_completo","post_criado_em"
            ])

        in_placeholders = ",".join(["%s"] * len(tutor_ids))

        query = f"""
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
                r.post_criado_em
            FROM
                (
                    SELECT
                        u.id AS tutor_id,
                        CONCAT_WS(' ', u.firstname, u.lastname) AS tutor_completo
                    FROM mdl_user u
                    WHERE u.id IN ({in_placeholders})
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
                        CONCAT_WS(' ', u2.firstname, u2.lastname) AS autor_aluno_completo,
                        FROM_UNIXTIME(parent.created) AS post_criado_em
                    FROM mdl_forum_posts p
                    JOIN mdl_user u ON u.id = p.userid
                    JOIN mdl_forum_discussions d ON d.id = p.discussion
                    JOIN mdl_forum f ON f.id = d.forum
                    JOIN mdl_forum_posts parent ON parent.id = p.parent
                    JOIN mdl_user u2 ON u2.id = parent.userid
                    WHERE f.course = %s
                    AND p.created >= UNIX_TIMESTAMP(%s)
                    AND p.created <  UNIX_TIMESTAMP(DATE_ADD(%s, INTERVAL 1 DAY))
                    AND p.userid IN ({in_placeholders})
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
        """
        params = []
        params.extend(tutor_ids)
        params.extend([subject_id, start_at, end_at])
        params.extend(tutor_ids)

        with connector.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)
    
    def fetch_tutors_login_subject(self, connector, subject_id, start_date, end_date, tutor_ids):
        tutor_ids = [int(x) for x in tutor_ids if x is not None]
        if not tutor_ids:
            return pd.DataFrame(columns=[
                "tutor_id", "firstname", "lastname",
                "first_login", "last_login",
                "first_course_access", "last_course_access",
                "n_login", "n_login_subject"
            ])

        in_placeholders = ",".join(["%s"] * len(tutor_ids))

        query = f"""
            SELECT 
                u.id AS tutor_id,
                u.firstname,
                u.lastname,

                FROM_UNIXTIME(MIN(CASE WHEN l.action = 'loggedin'
                                    THEN l.timecreated END)) AS first_login,
                FROM_UNIXTIME(MAX(CASE WHEN l.action = 'loggedin'
                                    THEN l.timecreated END)) AS last_login,

                FROM_UNIXTIME(MIN(CASE WHEN l.target = 'course'
                                        AND l.action IN ('viewed','entered')
                                    THEN l.timecreated END)) AS first_course_access,
                FROM_UNIXTIME(MAX(CASE WHEN l.target = 'course'
                                        AND l.action IN ('viewed','entered')
                                    THEN l.timecreated END)) AS last_course_access,

                SUM(CASE WHEN l.action = 'loggedin' THEN 1 ELSE 0 END) AS n_login,
                SUM(CASE WHEN l.target = 'course'
                        AND l.action IN ('viewed','entered')
                        THEN 1 ELSE 0 END) AS n_login_subject

            FROM mdl_user u
            LEFT JOIN mdl_logstore_standard_log l
                ON l.userid = u.id
            AND l.component = 'core'
            AND l.timecreated BETWEEN UNIX_TIMESTAMP(%s) AND UNIX_TIMESTAMP(%s)
            AND (
                    (l.action = 'loggedin')
                OR (l.courseid = %s AND l.target = 'course' AND l.action IN ('viewed','entered'))
            )
            WHERE u.id IN ({in_placeholders})
            GROUP BY u.id, u.firstname, u.lastname
            ORDER BY u.id;
        """

        params = [start_date, end_date, subject_id]
        params.extend(tutor_ids)

        with connector.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        df = pd.DataFrame(rows, columns=cols)

        if not df.empty:
            df["n_login"] = df["n_login"].fillna(0).astype(int)
            df["n_login_subject"] = df["n_login_subject"].fillna(0).astype(int)

        return df
    
    def fetch_tutors_access_days(self, connector, subject_id: int, start_date, end_date, tutor_ids):
        tutor_ids = [int(x) for x in tutor_ids if x is not None]
        if not tutor_ids:
            return pd.DataFrame(columns=["tutor_id", "access_day"])

        in_placeholders = ",".join(["%s"] * len(tutor_ids))

        query = f"""
            SELECT
                t.tutor_id,
                DATE(FROM_UNIXTIME(l.timecreated)) AS access_day
            FROM
                (
                    SELECT u.id AS tutor_id
                    FROM mdl_user u
                    WHERE u.id IN ({in_placeholders})
                ) AS t
            JOIN mdl_logstore_standard_log l
                ON l.userid = t.tutor_id
            AND l.component = 'core'
            AND l.timecreated BETWEEN UNIX_TIMESTAMP(%s) AND UNIX_TIMESTAMP(%s)
            AND (
                    (l.action = 'loggedin')
                OR (l.courseid = %s AND l.target = 'course' AND l.action IN ('viewed','entered'))
            )
            GROUP BY t.tutor_id, access_day
            ORDER BY t.tutor_id, access_day;
        """

        params = []
        params.extend(tutor_ids)
        params.extend([start_date, end_date, subject_id])

        with connector.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)

    def fetch_daily_events(self, connector, subject_id):
        with connector.cursor() as cur:
            cur.execute('''
                SELECT
                    DATE(FROM_UNIXTIME(timecreated)) AS day,
                    COUNT(*) AS events
                FROM mdl_logstore_standard_log
                WHERE courseid = %s AND action <> 'loggedin'
                        AND userid IS NOT NULL AND userid <> 0
                        AND (
                            target IN ('course','course_module')
                            OR component LIKE 'mod\\_%%'
                        )
                GROUP BY day
                ORDER BY day;
            ''', (subject_id, ))

            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)
    
    def fetch_subject_info_tutors(self, connector, subject_id, start_date, end_date):
        with connector.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    base.subject_id,

                    -- tutores ATIVOS no intervalo (tem pelo menos 1 log no range)
                    (
                        SELECT COUNT(DISTINCT ra_t.userid)
                        FROM mdl_role_assignments ra_t
                        JOIN mdl_context c_t ON c_t.id = ra_t.contextid
                        JOIN mdl_logstore_standard_log l_t
                        ON l_t.userid = ra_t.userid
                        AND l_t.courseid = c_t.instanceid
                        WHERE c_t.contextlevel = 50
                        AND c_t.instanceid = %s
                        AND ra_t.roleid IN (3,4,9,17)
                        AND FROM_UNIXTIME(l_t.timecreated) >= %s
                        AND FROM_UNIXTIME(l_t.timecreated) <  DATE_ADD(%s, INTERVAL 1 DAY)
                    ) AS total_tutors,

                    (
                        (
                            SELECT COUNT(DISTINCT ra_s.userid)
                            FROM mdl_role_assignments ra_s
                            JOIN mdl_context c_s ON c_s.id = ra_s.contextid
                            WHERE c_s.contextlevel = 50
                            AND c_s.instanceid = %s
                            AND ra_s.roleid = 5
                        )
                        /
                        NULLIF(
                            (
                                SELECT COUNT(DISTINCT ra_t.userid)
                                FROM mdl_role_assignments ra_t
                                JOIN mdl_context c_t ON c_t.id = ra_t.contextid
                                JOIN mdl_logstore_standard_log l_t
                                ON l_t.userid = ra_t.userid
                                AND l_t.courseid = c_t.instanceid
                                WHERE c_t.contextlevel = 50
                                AND c_t.instanceid = %s
                                AND ra_t.roleid IN (3,4,9,17)
                                AND FROM_UNIXTIME(l_t.timecreated) >= %s
                                AND FROM_UNIXTIME(l_t.timecreated) <  DATE_ADD(%s, INTERVAL 1 DAY)
                            ),
                            0
                        )
                    ) AS students_per_tutor,

                    logs.average_logs_per_day_per_tutor

                FROM
                (
                    SELECT c.id AS subject_id, c.fullname AS subject_name
                    FROM mdl_course c
                    WHERE c.id = %s
                ) AS base

                JOIN
                (
                    SELECT
                        sub.subject_id,
                        sub.subject_name,
                        AVG(sub.logs_per_tutor / NULLIF(sub.days_per_tutor, 0)) AS average_logs_per_day_per_tutor
                    FROM
                    (
                        SELECT
                            c.id AS subject_id,
                            c.fullname AS subject_name,
                            ra.userid,
                            COUNT(l.id) AS logs_per_tutor,
                            DATEDIFF(
                                MAX(FROM_UNIXTIME(l.timecreated)),
                                MIN(FROM_UNIXTIME(l.timecreated))
                            ) + 1 AS days_per_tutor
                        FROM mdl_course c
                        JOIN mdl_context ctx ON ctx.instanceid = c.id AND ctx.contextlevel = 50
                        JOIN mdl_role_assignments ra ON ra.contextid = ctx.id AND ra.roleid IN (3,4,9,17)
                        JOIN mdl_logstore_standard_log l ON l.userid = ra.userid AND l.courseid = c.id
                        WHERE c.id = %s
                        AND FROM_UNIXTIME(l.timecreated) >= %s
                        AND FROM_UNIXTIME(l.timecreated) <  DATE_ADD(%s, INTERVAL 1 DAY)
                        GROUP BY c.id, c.fullname, ra.userid
                    ) AS sub
                    GROUP BY sub.subject_id, sub.subject_name
                ) AS logs
                ON logs.subject_id = base.subject_id;
                ''',
                (
                    subject_id, start_date, end_date,      
                    subject_id,                             
                    subject_id, start_date, end_date,       
                    subject_id,                          
                    subject_id, start_date, end_date        
                )
            )

            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def fetch_tutors_names(self, connector=None, subject_id=None, user_id=None):
        """
        Mode A (by subject): subject_id -> retorna tutor_id + full_name (tutores do subject)
        Mode B (by user):    user_id    -> retorna tutor_id + full_name (apenas esse usuário)
        """
        if (subject_id is None and user_id is None) or (subject_id is not None and user_id is not None):
            raise ValueError("Passe exatamente um parâmetro: subject_id OU user_id.")

        with connector.cursor() as cur:
            if subject_id is not None:
                cur.execute(
                    """
                    SELECT DISTINCT
                        u.id AS tutor_id,
                        CONCAT(u.firstname, ' ', u.lastname) AS full_name
                    FROM mdl_context ctx
                    JOIN mdl_role_assignments ra ON ra.contextid = ctx.id
                    JOIN mdl_user u ON u.id = ra.userid
                    WHERE ctx.contextlevel = 50
                    AND ctx.instanceid = %s
                    ORDER BY full_name
                    """,
                    (subject_id,)
                )
            else:
                cur.execute(
                    """
                    SELECT
                        u.id AS tutor_id,
                        CONCAT(u.firstname, ' ', u.lastname) AS full_name
                    FROM mdl_user u
                    WHERE u.id = %s
                    """,
                    (user_id,)
                )

            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)
    
    def fetch_forum_messages_counts(self, connector, subject_id, start_at, end_at):
        with connector.cursor() as cur:
            cur.execute(
                """
                SELECT
                    f.id   AS forum_id,
                    f.name AS forum_name,

                    SUM(
                        CASE WHEN EXISTS (
                            SELECT 1
                            FROM mdl_role_assignments ra
                            JOIN mdl_context c ON c.id = ra.contextid
                            WHERE c.contextlevel = 50
                            AND c.instanceid    = %s
                            AND ra.userid       = p.userid
                            AND ra.roleid       = 5
                        ) THEN 1 ELSE 0 END
                    ) AS mensagens_alunos,

                    SUM(
                        CASE WHEN EXISTS (
                            SELECT 1
                            FROM mdl_role_assignments ra
                            JOIN mdl_context c ON c.id = ra.contextid
                            WHERE c.contextlevel = 50
                            AND c.instanceid    = %s
                            AND ra.userid       = p.userid
                            AND ra.roleid       IN (3,4,9,17)
                        ) THEN 1 ELSE 0 END
                    ) AS mensagens_tutores,
                    (
                        SUM(CASE WHEN EXISTS (
                            SELECT 1
                            FROM mdl_role_assignments ra
                            JOIN mdl_context c ON c.id = ra.contextid
                            WHERE c.contextlevel = 50
                            AND c.instanceid    = %s
                            AND ra.userid       = p.userid
                            AND ra.roleid       = 5
                        ) THEN 1 ELSE 0 END)
                        +
                        SUM(CASE WHEN EXISTS (
                            SELECT 1
                            FROM mdl_role_assignments ra
                            JOIN mdl_context c ON c.id = ra.contextid
                            WHERE c.contextlevel = 50
                            AND c.instanceid    = %s
                            AND ra.userid       = p.userid
                            AND ra.roleid       IN (3,4,9,17)
                        ) THEN 1 ELSE 0 END)
                    ) AS mensagens_total

                FROM mdl_forum_posts p
                JOIN mdl_forum_discussions d ON d.id = p.discussion
                JOIN mdl_forum f            ON f.id = d.forum

                WHERE f.course = %s
                AND p.created >= UNIX_TIMESTAMP(%s)
                AND p.created <  UNIX_TIMESTAMP(DATE_ADD(%s, INTERVAL 1 DAY))

                GROUP BY f.id, f.name
                ORDER BY f.name;
                """,
                (subject_id, subject_id, subject_id, subject_id, subject_id, start_at, end_at),
            )

            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)
    
    def fetch_tutor_summary(self, connector, subject_id, tutor_id):
        with connector.cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.id AS tutor_id,
                    CONCAT(u.firstname, ' ', u.lastname) AS full_name,
                    u.email AS email,
                    cc2.name AS degree_program,
                    r.name AS role,
                    g.name AS tutor_group,
                    FROM_UNIXTIME(ula.timeaccess) AS last_access,
                    (
                        SELECT FROM_UNIXTIME(MIN(ls.timecreated))
                        FROM mdl_logstore_standard_log ls
                        JOIN mdl_role_assignments ra2 ON ra2.userid = ls.relateduserid
                        JOIN mdl_role r2 ON r2.id = ra2.roleid
                        JOIN mdl_context ctx2 ON ctx2.id = ra2.contextid
                        WHERE ls.relateduserid = u.id
                        AND ls.courseid = c.id
                        AND r2.id IN (3,4,9,17)
                        AND ls.action = 'assigned'
                    ) AS tutor_since
                FROM mdl_course c
                LEFT JOIN mdl_course_categories cc3 ON cc3.id = c.category
                LEFT JOIN mdl_course_categories cc2 ON cc2.id = cc3.parent
                LEFT JOIN mdl_course_categories cc1 ON cc1.id = cc2.parent
                JOIN mdl_user u ON u.id = %s
                LEFT JOIN mdl_context ctx ON ctx.instanceid = c.id AND ctx.contextlevel = 50
                LEFT JOIN mdl_role_assignments ra ON ra.contextid = ctx.id AND ra.userid = u.id
                LEFT JOIN mdl_role r ON r.id = ra.roleid AND r.id IN (3,4,9,17)
                LEFT JOIN mdl_groups_members gm ON gm.userid = u.id
                LEFT JOIN mdl_groups g ON g.id = gm.groupid AND g.courseid = c.id
                LEFT JOIN mdl_user_lastaccess ula ON ula.userid = u.id AND ula.courseid = c.id
                WHERE c.id = %s
                ORDER BY ula.timeaccess DESC
                LIMIT 1;
                """,
                (tutor_id, subject_id),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)
    
    def fetch_institution_info_tutors(self, connector):
        with connector.cursor() as cur:
            cur.execute("""
                SELECT
                    (SELECT COUNT(DISTINCT u.id)
                        FROM mdl_role r
                        JOIN mdl_role_assignments ra ON ra.roleid = r.id
                        JOIN mdl_user u ON u.id = ra.userid
                        JOIN mdl_context c ON c.id = ra.contextid
                        WHERE c.contextlevel = 50
                            AND r.id IN (3,4,9,17)) AS total_tutors,

                    (SELECT AVG(num_tutors)
                        FROM (
                            SELECT
                                cc2.id AS degree_program_id,
                                COUNT(DISTINCT ra.userid) AS num_tutors
                            FROM mdl_course_categories cc1
                            JOIN mdl_course_categories cc2 ON cc2.parent = cc1.id
                            JOIN mdl_course_categories cc3 ON cc3.parent = cc2.id
                            JOIN mdl_course c ON c.category = cc3.id
                            LEFT JOIN mdl_context ctx ON ctx.instanceid = c.id AND ctx.contextlevel = 50
                            LEFT JOIN mdl_role_assignments ra ON ra.contextid = ctx.id AND ra.roleid IN (3,4,9,17)
                            GROUP BY cc2.id
                        ) AS tutor_counts) AS mean_tutors_per_degree_program,

                    (SELECT AVG(t.total_tutors)
                    FROM (
                        SELECT 
                            ctx.instanceid AS course_id,
                            COUNT(DISTINCT ra.userid) AS total_tutors
                        FROM mdl_role_assignments ra
                        JOIN mdl_context ctx ON ctx.id = ra.contextid
                        WHERE ctx.contextlevel = 50
                        AND ra.roleid IN (9, 17)
                        GROUP BY ctx.instanceid
                    ) AS t) AS mean_tutors_per_subject
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        df = pd.DataFrame(rows, columns=cols)
        return df   
    
    def fetch_tutors_feedback_subject(self, connector, subject_id, start_date, end_date, tutor_ids):
        tutor_ids = [int(x) for x in tutor_ids if x is not None]
        if not tutor_ids:
            return pd.DataFrame(columns=[
                "tutor_id", "tutor_nome", "papel",
                "n_corrections", "n_corrections_with_feedback",
                "n_textual_feedback", "n_feedback_pdf",
                "percentage_feedback"
            ])

        in_placeholders = ",".join(["%s"] * len(tutor_ids))

        query = f"""
            SELECT
                t.tutor_id,
                CONCAT(t.firstname, ' ', t.lastname) AS tutor_nome,
                t.papel,

                COUNT(a.gradeid)    AS n_corrections,
                SUM(a.tem_feedback) AS n_corrections_with_feedback,

                SUM(a.n_textual_feedback) AS n_textual_feedback,
                SUM(a.n_feedback_pdf)     AS n_feedback_pdf,

                CASE
                    WHEN COUNT(a.gradeid) > 0
                    THEN ROUND(SUM(a.tem_feedback) / COUNT(a.gradeid), 2)
                    ELSE 0
                END AS percentage_feedback

            FROM (
                SELECT
                    u.id        AS tutor_id,
                    u.firstname,
                    u.lastname,
                    'tutor'     AS papel
                FROM mdl_user u
                WHERE u.id IN ({in_placeholders})
            ) t

            LEFT JOIN (
                SELECT
                    g.id     AS gradeid,
                    g.grader AS tutor_id,

                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM mdl_assignfeedback_comments c
                            WHERE c.grade = g.id
                            AND c.commenttext IS NOT NULL
                            AND LENGTH(c.commenttext) > 0
                        )
                        OR EXISTS (
                            SELECT 1
                            FROM mdl_assignfeedback_editpdf_cmnt p
                            WHERE p.gradeid = g.id
                            AND p.rawtext IS NOT NULL
                            AND LENGTH(p.rawtext) > 0
                            AND p.draft = 0
                        )
                        THEN 1 ELSE 0
                    END AS tem_feedback,

                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM mdl_assignfeedback_comments c
                            WHERE c.grade = g.id
                            AND c.commenttext IS NOT NULL
                            AND LENGTH(c.commenttext) > 0
                        )
                        THEN 1 ELSE 0
                    END AS n_textual_feedback,

                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM mdl_assignfeedback_editpdf_cmnt p
                            WHERE p.gradeid = g.id
                            AND p.rawtext IS NOT NULL
                            AND LENGTH(p.rawtext) > 0
                            AND p.draft = 0
                        )
                        THEN 1 ELSE 0
                    END AS n_feedback_pdf

                FROM mdl_assign_grades g
                WHERE g.timemodified BETWEEN UNIX_TIMESTAMP(%s) AND UNIX_TIMESTAMP(%s)
                AND g.grader IN ({in_placeholders})
            ) a
                ON a.tutor_id = t.tutor_id

            GROUP BY
                t.tutor_id,
                t.firstname,
                t.lastname,
                t.papel
            ORDER BY percentage_feedback DESC;
        """

        params = []
        params.extend(tutor_ids)
        params.extend([start_date, end_date])
        params.extend(tutor_ids)

        with connector.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        df = pd.DataFrame(rows, columns=cols)

        if not df.empty:
            for c in ["n_corrections", "n_corrections_with_feedback", "n_textual_feedback", "n_feedback_pdf"]:
                df[c] = df[c].fillna(0).astype(int)
            df["percentage_feedback"] = df["percentage_feedback"].fillna(0).astype(float)

        return df
    
    def fetch_all_tutors(self, connector, subject_id, start_date, end_date):
        with connector.cursor() as cur:
            cur.execute(
                """
                SELECT
                    ls.relateduserid AS tutor_id,
                    CONCAT(u.firstname, ' ', u.lastname) AS full_name,
                    r.id AS role_id,
                    r.name AS role_assigned,
                    FROM_UNIXTIME(ls.timecreated) AS event_time,
                    ls.action AS role_action,
                    ctx.instanceid AS subject_id
                FROM mdl_logstore_standard_log ls
                JOIN mdl_context ctx ON ctx.id = ls.contextid
                        AND ctx.contextlevel = 50 AND ctx.instanceid = %s
                JOIN mdl_user u ON u.id = ls.relateduserid
                JOIN mdl_role r ON r.id = ls.objectid
                WHERE ls.target = 'role'
                    AND ls.action = 'assigned'
                    AND ls.objectid IN (3, 4, 9, 17)
                    AND ls.timecreated <= UNIX_TIMESTAMP(%s) 
                    AND NOT EXISTS (
                        SELECT 1
                        FROM mdl_logstore_standard_log ls2
                        JOIN mdl_context ctx2
                        ON ctx2.id = ls2.contextid
                        AND ctx2.contextlevel = 50
                        AND ctx2.instanceid = %s             
                        WHERE ls2.target = 'role'
                        AND ls2.action = 'unassigned'
                        AND ls2.objectid = ls.objectid
                        AND ls2.relateduserid = ls.relateduserid
                        AND ls2.timecreated <= UNIX_TIMESTAMP(%s) 
                    )
                ORDER BY ls.timecreated ASC;
                """,
                (subject_id, start_date, subject_id, end_date),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)
    
    def fetch_subjects_summary_tutors(self, connector):
        with connector.cursor() as cur:
            cur.execute("""
                SELECT
                    c.id AS subject_id,
                    c.fullname AS name,
                    c.shortname AS abbrev,
                    (
                        SELECT GROUP_CONCAT(DISTINCT CONCAT(u.firstname, ' ', u.lastname) SEPARATOR ', ')
                        FROM mdl_role_assignments ra
                        JOIN mdl_context ctx ON ctx.id = ra.contextid
                        JOIN mdl_user u ON u.id = ra.userid
                        WHERE ctx.contextlevel = 50
                          AND ctx.instanceid = c.id
                          AND ra.roleid IN (3, 4)
                    ) AS teachers,
                    (
                        SELECT COUNT(DISTINCT ra.userid)
                        FROM mdl_role_assignments ra
                        JOIN mdl_context ctx ON ctx.id = ra.contextid
                        WHERE ctx.contextlevel = 50
                          AND ctx.instanceid = c.id
                          AND ra.roleid = 5
                    ) AS total_students,
                    (
                        SELECT COUNT(DISTINCT ra.userid)
                        FROM mdl_role_assignments ra
                        JOIN mdl_context ctx ON ctx.id = ra.contextid
                        WHERE ctx.contextlevel = 50
                          AND ctx.instanceid = c.id
                          AND ra.roleid IN (9, 17)
                    ) AS total_tutors,
                    (
                        (
                            SELECT COUNT(DISTINCT ra.userid)
                            FROM mdl_role_assignments ra
                            JOIN mdl_context ctx ON ctx.id = ra.contextid
                            WHERE ctx.contextlevel = 50
                              AND ctx.instanceid = c.id
                              AND ra.roleid = 5
                        )
                        /
                        NULLIF(
                            (
                                SELECT COUNT(DISTINCT ra.userid)
                                FROM mdl_role_assignments ra
                                JOIN mdl_context ctx ON ctx.id = ra.contextid
                                WHERE ctx.contextlevel = 50
                                  AND ctx.instanceid = c.id
                                  AND ra.roleid IN (9, 17)
                            ),
                            0
                        )
                    ) AS students_per_tutor

                FROM mdl_course c
                WHERE c.id != 1
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        return pd.DataFrame(rows, columns=cols)
    