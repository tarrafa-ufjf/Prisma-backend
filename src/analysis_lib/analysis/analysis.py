from ..mapper.map import Mapper
from .Engajamento.engagement import Engagement
from .Desempenho.performance import Performance
from .Motivacao.motivation import Motivation
from .Pedagogico.pedagogic import Pedagogic
from .Cognitivo.cognitive import Cognitive
from .Give_Up.give_up import Give_Up

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
    
    def general_pedagogic_analysis(self, connector, version, analysis_config):
        pedagogic = Pedagogic(self.mapper)
        analysis_config = pedagogic.general_analysis(version, connector, analysis_config)

        return analysis_config
    
    def general_give_up_analysis(self, connector, version, analysis_config):
        give_up = Give_Up(self.mapper)
        analysis_config = give_up.general_analysis(version, connector, analysis_config)

        return analysis_config

    def engagement_analysis(self, subject_id, type_query, version, connector, student_id = None):
        engagement = Engagement(self.mapper)
        res = None

        if type_query == 'user':
            res = engagement.student_analysis(subject_id, student_id, version, connector)
        elif type_query == 'course': 
            res = engagement.course_analysis(subject_id, version, connector)
        return res
    
    def performance_analysis(self, subject_id, type_query, version, connector, student_id = None):
        performance = Performance(self.mapper)
        res = None

        if type_query == 'user':
            res = performance.student_analysis(subject_id, student_id, version, connector)
        elif type_query == 'course': 
            res = performance.course_analysis(subject_id, version, connector)

        return res
    
    def motivation_analysis(self, subject_id, type_query, version, connector, student_id = None):
        motivation = Motivation(self.mapper)
        res = None

        if type_query == 'user':
            res = motivation.student_analysis(subject_id, student_id, version, connector)
        elif type_query == 'course': 
            res = motivation.course_analysis(subject_id, version, connector)

        return res
    
    def pedagogic_analysis(self, subject_id, type_query, version, connector):
        pedagogic = Pedagogic(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'course': 
            res = pedagogic.course_analysis(subject_id, version, connector)

        return res
    
    def cognitive_analysis(self, subject_id, type_query, version, connector, student_id = None):
        cognitive = Cognitive(self.mapper)
        res = None

        if type_query == 'user':
            res = cognitive.student_analysis(subject_id, student_id, version, connector)
        elif type_query == 'course': 
            res = cognitive.course_analysis(subject_id, version, connector)

        return res
    
    def give_up_analysis(self, subject_id, type_query, version, connector, student_id = None):
        give_up = Give_Up(self.mapper)
        res = None

        if type_query == 'user':
            res = give_up.student_analysis(subject_id, student_id, version, connector)
        elif type_query == 'course': 
            res = give_up.course_analysis(subject_id, version, connector)

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

    def indicators_analysis(self, subject_id, type_query, version, connector, student_id=None):
        if type_query == 'user':
            eng = self.engagement_analysis(subject_id, 'user', version, connector, student_id) or {}
            mot = self.motivation_analysis(subject_id, 'user', version, connector, student_id) or {}
            per = self.performance_analysis(subject_id, 'user', version, connector, student_id) or {}
            cog = self.cognitive_analysis(subject_id, 'user', version, connector, student_id) or {}
            gu  = self.give_up_analysis(subject_id, 'user', version, connector, student_id) or {}

            return {
                "subject_id": subject_id,
                "student_id": student_id,
                "indicators": {
                    "engagement": eng.get("posts_required_label"),
                    "motivation": mot.get("posts_unrequired_label"),
                    "performance": per.get("performance_label"),
                    "cognitive": cog.get("label"),
                    "give_up": gu.get("give_up")
                },
            }

        elif type_query == 'subject':
            from .Indicators_Percentual.indicators_percentual import Indicators_Percentual
            return Indicators_Percentual(self.mapper).subject_analysis(subject_id)

        else:
            raise ValueError("type_query inválido. Use 'user' ou 'subject'.")
    
    
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
    
    def get_subject_student_summary(self, subject_id, student_id, version, connector):
        from .Student.Student_Summary.summary import Student_Summary
        student_summary = Student_Summary(self.mapper)

        return student_summary.subject_analysis(subject_id, student_id, version, connector)
    
    def get_subject_student_grades(self, subject_id, student_id, version, connector):
        from .Student.Student_Grades.grades import Student_Grades
        student_grades = Student_Grades(self.mapper)

        return student_grades.subject_analysis(subject_id, student_id, version, connector)
    
    # def get_subject_student_engagement(self, subject_id, student_id, version, connector):
    #     from .Student.Engagement.engagement import Engagement
    #     student_engagement = Engagement(self.mapper)

    #     return student_engagement.subject_analysis(subject_id, student_id, version, connector)

