'''
Neste arquivo, devemos criar a lógica do mapeamento das consultas.
'''
import re
from .connectors.moodle3_1 import Moodle31

class Mapper:
    def __init__(self):
        pass

    def get_real_version(self, old):
        pattern = r'[1-9]\d*\.\d+\.\d+'
        resultado = re.search(pattern, old)
        if resultado:
            return resultado.group()
        return None

    # Função responsável por identificar a versão do moodle utilizada
    def get_moodle_version(self, connector):
        cursor = connector.cursor()
        cursor.execute(f"""
            SELECT name, value
            FROM mdl_config
            WHERE name = 'release'
        """)
        result = cursor.fetchall() 
        cursor.close()

        version = result[0]['value']
        version = self.get_real_version(version)

        return version
    
    # Funções responsáveis por mapear as consultas com base na versão do moodle
    def get_moodle(self, connector, version):
        match version:
            case '3.1.3':
                return Moodle31(connector)
            case _:
                raise ValueError("Unsupported Moodle version")

    def get_general_query(self, connector, version):
        moodle = self.get_moodle(connector, version)
        connector.close()
        return moodle.general_indicators()

    def get_engagement_data(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_all_posts_for_forum_required_by_course(subject_id)
    
    def get_all_students(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_all_students_by_course(subject_id)
    
    def get_courses(self, connector, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_courses()
    
    def get_activity_weights(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_activity_weights(subject_id)
    
    def get_grades_by_course(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_grades_by_course(subject_id)
    
    def get_foruns_non_required(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_foruns_non_required_by_course(subject_id)

    def get_forum_data(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_forum_data(subject_id)
    
    def get_course_forum_viewed(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_course_forum_viewed(subject_id)
    
    def get_forum_post_created(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_forum_post_created(subject_id)
    
    def forum_reply_viewed(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.forum_reply_viewed(subject_id)
    
    def get_assign_submission_status_viewed(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_assign_submission_status_viewed(subject_id)
    
    def get_assign_assessable_submitted(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_assign_assessable_submitted(subject_id)
    
    def get_assign_feedback_viewed(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_assign_feedback_viewed(subject_id)
    
    def get_quizz_viewed(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_quizz_viewed(subject_id)
    
    def get_quizz_attempt_submitted(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_quizz_attempt_submitted(subject_id)
    
    def get_quizz_attempt_reviewd(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_quizz_attempt_reviewd(subject_id)
    
    def fetch_subject_info(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_subject_info(subject_id)
    
    def fetch_subject_metrics(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_subject_metrics(subject_id)
    
    def get_pct_usage_resource(self, connector, subject_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_pct_usage_resource(subject_id)
    
    def get_all_subjects(self, connector, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_all_subjects()
    
    def fetch_student_summary(self, subject_id, student_id, connector, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_student_summary(subject_id, student_id)
    
    def fetch_student_grades(self, subject_id, student_id, connector, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_student_grades(subject_id, student_id)
    
    def fetch_subjects_summary(self, connector, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_subjects_summary(connector)
    
    def fetch_institution_info(self, connector, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_institution_info(connector)
    
    def fetch_responses_forums(self, connector, version, subject_id, start_at, end_at):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_responses_forums(connector, subject_id, start_at, end_at)
    
    def fetch_tutors_login_subject(self, connector, version, subject_id, start_date, end_date):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_tutors_login_subject(connector, subject_id, start_date, end_date)
    
    def fetch_daily_events(self, connector, version, subject_id):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_daily_events(connector, subject_id)
    
    def fetch_subject_info_tutors(self, connector, version, subject_id, start_date, end_date):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_subject_info_tutors(subject_id, start_date, end_date)
    

    def fetch_tutors_names(self, connector, version, subject_id):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_tutors_names(connector, subject_id)
    
    
