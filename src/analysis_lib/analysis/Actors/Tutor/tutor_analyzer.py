from .Forums_Response.forums_response import Forums_Response
from .Analysis_login.analysis_login import Analysis_login
from .Subject.Indicators.Response_Forums.response_foruns import Response_Forums
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
    
    def response_foruns_analysis(self, subject_id, type_query, version, connector, user_id=None):
        response_foruns = Response_Forums(self.mapper)
        if type_query == "user":
            return response_foruns.student_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return response_foruns.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")