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
    
    # Função responsável por escolher qual código de consulta será utilzado baseando-se na versão do moodle
    def get_general_query(self, connector, version):
        match version:
            case '3.1.3':
                moodle = Moodle31(connector)
                return moodle.general_indicators()

    def get_engagement_data(self, connector, course_id, version):
        match version:
            case '3.1.3':
                moodle = Moodle31(connector)
                return moodle.get_all_posts_for_forum_required_by_course(course_id)
            case _:
                raise ValueError("Unsupported Moodle version")
    
    
