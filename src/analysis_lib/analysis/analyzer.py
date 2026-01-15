from ..mapper.map import Mapper
from .Actors.Student.student_analyzer import StudentAnalyzer
from .Actors.Tutor.tutor_analyzer import TutorAnalyzer

class Analyzer:
    def __init__(self):
        self.mapper = Mapper()

        self._actors = {
            "student": StudentAnalyzer(self.mapper),
            "tutor": TutorAnalyzer(self.mapper),
        }

    def _actor(self, actor: str):
        if actor not in self._actors:
            raise ValueError(f"invalid actor: {actor}. Use 'student' or 'tutor'.")
        return self._actors[actor]

    def get_moodle_version(self, connector):
        return self.mapper.get_moodle_version(connector)

    def engagement_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="student"):
        return self._actor(actor).engagement_analysis(subject_id, type_query, version, connector, user_id=user_id)

    def performance_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="student"):
        return self._actor(actor).performance_analysis(subject_id, type_query, version, connector, user_id=user_id)

    def motivation_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="student"):
        return self._actor(actor).motivation_analysis(subject_id, type_query, version, connector, user_id=user_id)

    def pedagogic_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="student"):
        return self._actor(actor).pedagogic_analysis(subject_id, type_query, version, connector, user_id=user_id)

    def cognitive_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="student"):
        return self._actor(actor).cognitive_analysis(subject_id, type_query, version, connector, user_id=user_id)

    def give_up_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="student"):
        return self._actor(actor).give_up_analysis(subject_id, type_query, version, connector, user_id=user_id)

    def indicators_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="student"):
        return self._actor(actor).indicators_analysis(subject_id, type_query, version, connector, user_id=user_id)
    
    def response_foruns(self, subject_id, type_query, version, connector, start_at, end_at, user_id=None, actor="tutor"):
        return self._actor(actor).response_foruns(subject_id, type_query, version, connector, start_at, end_at, user_id=user_id)
    
    def analysis_login(self, subject_id, type_query, version, connector,start_at, end_at, user_id=None, actor="tutor"):
        return self._actor(actor).analysis_login(subject_id, type_query, version, connector, start_at, end_at, user_id=user_id)
    
    def get_all_subjects(self, version, connector):
        from .Actors.Student.General.subjects import Subjects
        subjects = Subjects(self.mapper)

        return subjects.get_subjects(version, connector)
    
    def general_subjects_indicators(self, version, connector):
        from .Actors.Student.General.general_subjects_indicators import General_subjects_indicators

        general = General_subjects_indicators(self.mapper)
        return general.general_subjects_indicators(version, connector)
    
    def general_indicators(self, version, connector):
        from .Actors.Student.General.general_indicators import General_indicators

        general = General_indicators(self.mapper)
        return general.general_indicators(version, connector)
    
    def general_summary(self, version, connector):
        from .Actors.Student.General.general_summary import General_summary

        general = General_summary(self.mapper)
        return general.general_summary(version, connector)
    
    def summary_analysis(self, subject_id, type_query, version, connector):
        from .Actors.Student.Subject.Summary.summary import Summary
        summary = Summary(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'subject': 
            res = summary.subject_analysis(subject_id, version, connector)

        return res
    
    def info_graphs_analysis(self, subject_id, type_query, version, connector):
        from .Actors.Student.Subject.Info_Graphs.info_graphs import Info_Graphs
        info_graphs = Info_Graphs(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'subject': 
            res = info_graphs.info_graphs(subject_id, version, connector)

        return res

    def rankings_analysis(self, entity_id: int, scope: str, version, connector, kind: str = "best-performance", limit: int = 10):
        from .Actors.Student.Subject.Rankings.rankings import Rankings  
        rankings = Rankings(self.mapper)

        if scope == 'user':
            pass
        elif scope == 'subject':
            return rankings.subject_analysis(entity_id, version, connector, kind=kind, limit=limit)
        else:
            raise ValueError("invalid scope")
    
    def get_subject_student_summary(self, subject_id, student_id, version, connector):
        from .Actors.Student.Student.Summary.summary import Student_Summary
        student_summary = Student_Summary(self.mapper)

        return student_summary.subject_analysis(subject_id, student_id, version, connector)
    
    def get_subject_student_grades(self, subject_id, student_id, version, connector):
        from .Actors.Student.Student.Grades.grades import Student_Grades
        student_grades = Student_Grades(self.mapper)

        return student_grades.subject_analysis(subject_id, student_id, version, connector)
    
    def rankings_general_analysis(self, version, connector, kind: str = "best-performance", limit: int = 10):
        from .Actors.Student.Subject.Rankings.rankings import Rankings  
        rankings = Rankings(self.mapper)

        return rankings.general_analysis(version, connector, kind=kind, limit=limit)
    
    def tutor_summary_analysis(self, subject_id, type_query, version, connector):
        from .Actors.Tutor.Subject.Summary.summary import Summary
        summary = Summary(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'subject': 
            res = summary.subject_analysis(subject_id, version, connector)
            print(res)

        return res
    
    def tutors_indicators_analysis(self, subject_id, type_query, version, connector):
        from .Actors.Tutor.Subject.Indicators_Percentual.indicators_percentual import Indicators_Percentual
        indicators_percentual = Indicators_Percentual(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'subject': 
            res = indicators_percentual.subject_analysis(subject_id)
            print(res)

        return res
    
    def tutors_rankings_analysis(self, entity_id: int, scope: str, version, connector, kind: str = "best-performance", limit: int = 10):
        from .Actors.Tutor.Subject.Rankings.rankings import Rankings  
        rankings = Rankings(self.mapper)

        if scope == 'user':
            pass
        elif scope == 'subject':
            return rankings.subject_analysis(entity_id, version, connector, kind=kind, limit=limit)
        else:
            raise ValueError("invalid scope")
        
    def tutors_interaction_channels(self, subject_id, type_query, version, connector):
        from .Actors.Tutor.Subject.Interaction_Channels.interaction_channels import Interaction_Channels
        interaction_channels = Interaction_Channels(self.mapper)
        res = None

        if type_query == 'user':
            pass
        elif type_query == 'subject': 
            res = interaction_channels.subject_analysis(subject_id, version, connector)

        return res
    
    def response_foruns_analysis(self, subject_id, type_query, version, connector, user_id=None, actor="tutor"):
        return self._actor(actor).response_foruns_analysis(subject_id, type_query, version, connector, user_id=user_id)