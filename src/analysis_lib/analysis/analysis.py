from ..mapper.map import Mapper
from .Engajamento.engagement import Engagement
from .Desempenho.performance import Performance
from .Motivacao.motivation import Motivation
from .Pedagogico.pedagogic import Pedagogic
from .Cognitivo.cognitive import Cognitive

class Analyzer:
    def __init__(self):
        self.mapper = Mapper()

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
    
    def general_cognitive_analysis(self, connector, version, analysis_config):
        cognitive = Cognitive(self.mapper)
        analysis_config = cognitive.general_analysis(version, connector, analysis_config)

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
    
    def cognitive_analysis(self, course_id, type_query, version, connector):
        from .Cognitivo.cognitive import Cognitive
        cognitive = Cognitive(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'course': 
            res = cognitive.course_analysis(course_id, version, connector)

        return res
    
    def summary_analysis(self, subject_id, type_query, version, connector):
        from .Summary.summary import Summary
        summary = Summary(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'subject': 
            res = summary.subject_analysis(subject_id, version, connector)

        return res
    
    def info_graphs_analysis(self, subject_id, type_query, version, connector):
        from .Info_Graphs.info_graphs import Info_Graphs
        info_graphs = Info_Graphs(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'subject': 
            res = info_graphs.info_graphs(subject_id, version, connector)

        return res

    def rankings_analysis(self, entity_id: int, scope: str, version, connector, kind: str = "best-performance", limit: int = 10):
        from .Rankings.rankings import Rankings  
        rankings = Rankings(self.mapper)

        if scope == 'user':
            pass
        elif scope == 'subject':
            return rankings.subject_analysis(entity_id, version, connector, kind=kind, limit=limit)
        else:
            raise ValueError("invalid scope")
        
    def get_all_subjects(self, version, connector):
        from .General.subjects import Subjects
        subjects = Subjects(self.mapper)

        return subjects.get_subjects(version, connector)
