from mapper.map import Mapper
import pandas as pd
from analysis.Engajamento.engagement import Engagement

class Analyzer:
    def __init__(self):
        self.mapper = Mapper()

    #Função temporária, apenas para testes
    def get_moodle_version(self, connector):
        return self.mapper.get_moodle_version(connector)

    def general_query(self, connector, version):
        return self.mapper.get_general_query(connector, version)
    
    def generate_course_csv(self, course_id):
        pass

    def engagement_analysis(self, course_id, type_query, version, connector):
        engagement = Engagement(self.mapper)

        if type_query == 'geral':
            pass
        elif type_query == 'periodo':
            pass
        elif type_query == 'usuario':
            pass
        elif type_query == 'course': 
            res = engagement.course_analysis(course_id, version, connector)
        elif type_query == 'detalhada':
            pass

        # Teste
        return res