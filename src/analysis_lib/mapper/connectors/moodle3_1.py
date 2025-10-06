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
    
    '''
    Consultas relacionadas ao indicador de profundidade cognitiva::
    '''

    # Fóruns
    def get_course_forum_viewed(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_forum_post_created(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def forum_reply_viewed(self, course_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT 
                    p.userid AS user_id,
                    d.id AS discussion_id,
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    # Assign
    def get_assign_submission_status_viewed(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_assign_assessable_submitted(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_assign_feedback_viewed(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    # Quizzes
    def get_quizz_viewed(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_quizz_attempt_submitted(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def get_quizz_attempt_reviewd(self, course_id):
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
            ''', (course_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    '''
    Consultas relacionadas as informações gerais das disciplinas para povoar as telas:
    '''
    def fetch_class_info(self, class_id):
        conn = self.connector
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    c.id        AS class_id,
                    c.fullname  AS name,
                    c.shortname AS abrev,
                    FROM_UNIXTIME(c.timecreated) AS date
                FROM mdl_course c
                WHERE c.id = %s;
            ''', (class_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    
    def fetch_class_metrics(self, class_id):
        conn = self.connector
        with conn.cursor() as cur:
            # 1) Total de alunos
            cur.execute('''
                SELECT COUNT(DISTINCT ue.userid) AS total_enrolled
                FROM mdl_enrol e
                JOIN mdl_user_enrolments ue ON ue.enrolid = e.id
                JOIN mdl_role_assignments ra ON ra.userid = ue.userid
                JOIN mdl_role r ON r.id = ra.roleid
                JOIN mdl_context ctx ON ctx.id = ra.contextid
                WHERE e.courseid = %s
                AND ctx.contextlevel = 50
                AND r.archetype = 'student';
            ''', (class_id,))
            total_rows = cur.fetchall()
            total_enrolled = total_rows[0]["total_enrolled"] if total_rows else 0

            # 2) Média de notas
            cur.execute('''
                SELECT ROUND(AVG(gg.finalgrade), 2) AS avg_grade_all
                FROM mdl_grade_grades gg
                JOIN mdl_grade_items gi ON gi.id = gg.itemid
                WHERE gi.itemtype = 'course'
                AND gi.courseid = %s;
            ''', (class_id,))
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
            ''', (class_id, class_id))
            rate_rows = cur.fetchall()
            taxa_aprovacao = rate_rows[0]["taxa_aprovacao"] if rate_rows else None

        data = [{
            "total_enrolled": int(total_enrolled or 0),
            "avg_grade_all": float(avg_grade_all) if avg_grade_all is not None else None,
            "taxa_aprovacao": float(taxa_aprovacao) if taxa_aprovacao is not None else None,
        }]
        df = pd.DataFrame(data)
        return df
        
        
