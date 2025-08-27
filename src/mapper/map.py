'''
Neste arquivo, devemos criar a lógica do mapeamento das consultas.
'''
import re
from mapper.connectors.moodle3_1 import Moodle31

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
