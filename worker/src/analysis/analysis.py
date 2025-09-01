from mapper.map import Mapper
import pandas as pd
from analysis.Engajamento.engagement import Engagement
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

class Analyzer:
    def __init__(self):
        self.mapper = Mapper()
        self.global_engagement: Optional[object] = None

    #Função temporária, apenas para testes
    def get_moodle_version(self, connector):
        return self.mapper.get_moodle_version(connector)

    def general_query(self, connector, version):
        self.global_engagement = self.engagement_analysis(None, 'geral', version, connector)

    def engagement_analysis(self, course_id, type_query, version, connector):
        engagement = Engagement(self.mapper)
        res = None

        if type_query == 'geral':
            res = engagement.general_analysis(version, connector)
        elif type_query == 'usuario':
            pass
        elif type_query == 'course': 
            res = engagement.course_analysis(course_id, version, connector)

        return res