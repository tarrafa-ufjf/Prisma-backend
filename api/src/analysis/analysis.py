from mapper.map import Mapper
import pandas as pd
from analysis.Engajamento.engagement import Engagement
from analysis.Desempenho.performance import Performance
from analysis.Motivacao.motivation import Motivation
from analysis.Pedagogico.pedagogic import Pedagogic
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
    
    def general_performance_analysis(self, connector, version, analysis_config):
        performance = Performance(self.mapper)
        analysis_config = performance.general_analysis(version, connector, analysis_config)

        return analysis_config
    
    def general_motivation_analysis(self, connector, version, analysis_config):
        motivation = Motivation(self.mapper)
        analysis_config = motivation.general_analysis(version, connector, analysis_config)

        return analysis_config

    def engagement_analysis(self, course_id, type_query, version, connector):
        engagement = Engagement(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'course': 
            res = engagement.course_analysis(course_id, version, connector)
        return res
    
    def performance_analysis(self, course_id, type_query, version, connector):
        performance = Performance(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'course': 
            res = performance.discretized_performance(course_id, version, connector)

        return res
    
    def motivation_analysis(self, course_id, type_query, version, connector):
        motivation = Motivation(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'course': 
            res = motivation.course_analysis(course_id, version, connector)

        return res
    
    def pedagogic_analysis(self, course_id, type_query, version, connector):
        pedagogic = Pedagogic(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'course': 
            res = pedagogic.course_analysis(course_id, version, connector)

        return res