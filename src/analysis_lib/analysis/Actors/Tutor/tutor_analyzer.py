from .Forums_Response.forums_response import Forums_Response
class TutorAnalyzer:
    def __init__(self, mapper):
        self.mapper = mapper

    def _not_implemented(self, name: str):
        raise NotImplementedError(f"{name} for tutor is not implemented yet")

    def response_foruns(self, subject_id, type_query, version, connector, user_id=None):
        forums_response = Forums_Response(self.mapper)
        if type_query == "user":
            return forums_response.tutors_analysis(subject_id, user_id, version, connector)
        if type_query == "subject":
            return forums_response.subject_analysis(subject_id, version, connector)
        raise ValueError("invalid type_query")