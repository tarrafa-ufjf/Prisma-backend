from mapper.map import Mapper
import pandas as pd
from analysis.Engajamento.engagement import Engagement
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional
from database import Database

class Analyzer:
    def __init__(self):
        self.mapper = Mapper()
        self.global_engagement: Optional[object] = None

    #Função temporária, apenas para testes
    def get_moodle_version(self, connector):
        return self.mapper.get_moodle_version(connector)

    def general_engagement_analysis(self, connector, version, analysis_config):
        engagement = Engagement(self.mapper)
        analysis_config = engagement.general_analysis(version, connector, analysis_config)

        return analysis_config

    def engagement_analysis(self, course_id, type_query, version, connector):
        engagement = Engagement(self.mapper)
        res = None

        if type_query == 'usuario':
            pass
        elif type_query == 'course': 
            res = engagement.course_analysis(course_id, version, connector)

        return res