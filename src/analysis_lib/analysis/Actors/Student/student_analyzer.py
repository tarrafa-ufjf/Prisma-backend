from .Engagement.engagement import Engagement
from .Performance.performance import Performance
from .Motivation.motivation import Motivation
from .Pedagogic.pedagogic import Pedagogic
from .Cognitive.cognitive import Cognitive
from .Give_Up.give_up import Give_Up

class StudentAnalyzer:
    def __init__(self, mapper):
        self.mapper = mapper

    def engagement_analysis(self, subject_id, type_query, version, connector, user_id=None):
        engagement = Engagement(self.mapper)
        if type_query == "user":
            return engagement.student_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return engagement.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")

    def performance_analysis(self, subject_id, type_query, version, connector, user_id=None):
        performance = Performance(self.mapper)
        if type_query == "user":
            return performance.student_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return performance.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")

    def motivation_analysis(self, subject_id, type_query, version, connector, user_id=None):
        motivation = Motivation(self.mapper)
        if type_query == "user":
            return motivation.student_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return motivation.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")

    def pedagogic_analysis(self, subject_id, type_query, version, connector, user_id=None):
        pedagogic = Pedagogic(self.mapper)
        if type_query == "user":
            return pedagogic.student_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return pedagogic.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")

    def cognitive_analysis(self, subject_id, type_query, version, connector, user_id=None):
        cognitive = Cognitive(self.mapper)
        if type_query == "user":
            return cognitive.student_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return cognitive.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")

    def give_up_analysis(self, subject_id, type_query, version, connector, user_id=None):
        give_up = Give_Up(self.mapper)
        if type_query == "user":
            return give_up.student_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return give_up.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")

    def indicators_analysis(self, subject_id, type_query, version, connector, user_id=None):
        if type_query == "user":
            eng = self.engagement_analysis(subject_id, "user", version, connector, user_id) or {}
            mot = self.motivation_analysis(subject_id, "user", version, connector, user_id) or {}
            per = self.performance_analysis(subject_id, "user", version, connector, user_id) or {}
            cog = self.cognitive_analysis(subject_id, "user", version, connector, user_id) or {}
            ped = self.pedagogic_analysis(subject_id, "user", version, connector, user_id) or {}
            gu  = self.give_up_analysis(subject_id, "user", version, connector, user_id) or {}

            return {
                "subject_id": subject_id,
                "student_id": user_id,  
                "indicators": {
                    "engagement": eng.get("posts_required_label"),
                    "motivation": mot.get("posts_unrequired_label"),
                    "performance": per.get("performance_label"),
                    "cognitive": cog.get("label"),
                    "ped": ped.get("label_relation_teacher_student"),
                    "give_up": gu.get("give_up"),
                },
            }

        if type_query == "subject":
            from ...Indicators_Percentual.indicators_percentual import Indicators_Percentual
            return Indicators_Percentual(self.mapper).subject_analysis(subject_id)

        raise ValueError("invalid type_query")