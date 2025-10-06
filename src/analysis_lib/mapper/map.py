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

    def get_engagement_data(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_all_posts_for_forum_required_by_course(course_id)
    
    def get_all_students(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_all_students_by_course(course_id)
    
    def get_courses(self, connector, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_courses()
    
    def get_activity_weights(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_activity_weights(course_id)
    
    def get_grades(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_grades_by_course(course_id)
    
    def get_foruns_non_required(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_foruns_non_required_by_course(course_id)

    def get_forum_data(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_forum_data(course_id)
    
    def get_private_messages(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_private_messages(course_id)
    
    def get_tutor_access_frequency(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_tutor_access_frequency(course_id)
    
    def get_course_forum_viewed(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_course_forum_viewed(course_id)
    
    def get_forum_post_created(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_forum_post_created(course_id)
    
    def forum_reply_viewed(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.forum_reply_viewed(course_id)
    
    def get_assign_submission_status_viewed(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_assign_submission_status_viewed(course_id)
    
    def get_assign_assessable_submitted(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_assign_assessable_submitted(course_id)
    
    def get_assign_feedback_viewed(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_assign_feedback_viewed(course_id)
    
    def get_quizz_viewed(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_quizz_viewed(course_id)
    
    def get_quizz_attempt_submitted(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_quizz_attempt_submitted(course_id)
    
    def get_quizz_attempt_reviewd(self, connector, course_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.get_quizz_attempt_reviewd(course_id)
    
    def fetch_class_info(self, connector, class_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_class_info(class_id)
    
    def fetch_class_metrics(self, connector, class_id, version):
        moodle = self.get_moodle(connector, version)
        return moodle.fetch_class_metrics(class_id)