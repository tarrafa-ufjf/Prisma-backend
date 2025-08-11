from mapper.map import Mapper
import pandas as pd

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