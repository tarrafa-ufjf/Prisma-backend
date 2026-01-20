from .Forums_Response.forums_response import Forums_Response
from .Analysis_login.analysis_login import Analysis_login
from .Analysis_feedback.analysis_feedback import Analysis_Feedback
from .Subject.Indicators.Response_Forums.response_foruns import Response_Forums
from .Subject.Indicators.Access.access import Access
class TutorAnalyzer:
    def __init__(self, mapper):
        self.mapper = mapper

    def _not_implemented(self, name: str):
        raise NotImplementedError(f"{name} for tutor is not implemented yet")

    def response_foruns(self, subject_id, type_query, version, connector, start_at, end_at, user_id=None):
        forums_response = Forums_Response(self.mapper)
        if type_query == "user":
            return forums_response.tutors_analysis(subject_id, user_id, version, connector, start_at, end_at)
        if type_query == "subject":
            return forums_response.subject_analysis(subject_id, version, connector, start_at, end_at)
        raise ValueError("invalid type_query")
    
    def analysis_login(self, subject_id, type_query, version, connector, start_at, end_at, user_id=None):
        forums_response = Analysis_login(self.mapper)
        if type_query == "user":
            return forums_response.tutors_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return forums_response.subject_analysis(subject_id, version, connector, start_at, end_at)
        raise ValueError("invalid type_query")
    
    def analysis_feedback(self, subject_id, type_query, version, connector, start_at, end_at, user_id=None):
        forums_response = Analysis_Feedback(self.mapper)
        if type_query == "user":
            return forums_response.tutors_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return forums_response.subject_analysis(subject_id, version, connector, start_at, end_at)
        raise ValueError("invalid type_query")
    
    def response_foruns_analysis(self, subject_id, type_query, route, version, connector, user_id=None):
        response_foruns = Response_Forums(self.mapper)
        if type_query == "user":
            return response_foruns.tutors_analysis(subject_id, user_id, version, connector, route)
        if type_query == "subject":
            return response_foruns.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")
    
    def access_analysis(self, subject_id, type_query, route, version, connector, user_id=None):
        access = Access(self.mapper)
        if type_query == "user":
            return access.tutors_analysis(subject_id, user_id, version, connector, route)
        if type_query == "subject":
            return access.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")
    
    def indicators_analysis(self, subject_id, type_query, route, version, connector, user_id=None):
        if type_query == "user":
            res = self.response_foruns_analysis(subject_id, "user", route, version, connector, user_id) or {}
            access = self.access_analysis(subject_id, "user", route, version, connector, user_id) or {}

            return {
                "subject_id": subject_id,
                "student_id": user_id,  
                "indicators": {
                    "response_foruns": res.get("label_forums_response"),
                    "access": access.get("label_access"),
                },
            }

        if type_query == "subject":
            from ...Actors.Tutor.Subject.Indicators_Percentual.indicators_percentual import Indicators_Percentual
            indicators_percentual = Indicators_Percentual(self.mapper)
            return indicators_percentual.subject_analysis(subject_id)
        
        raise ValueError("invalid type_query")