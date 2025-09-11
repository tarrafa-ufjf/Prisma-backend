from flask import jsonify
from mapper.moodle import Moodle
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