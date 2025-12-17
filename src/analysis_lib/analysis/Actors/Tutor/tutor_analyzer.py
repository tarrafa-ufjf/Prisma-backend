class TutorAnalyzer:
    def __init__(self, mapper):
        self.mapper = mapper

    def _not_implemented(self, name: str):
        raise NotImplementedError(f"{name} for tutor is not implemented yet")

    def engagement_analysis(self, subject_id, type_query, version, connector, user_id=None):
        return self._not_implemented("engagement_analysis")

    def performance_analysis(self, subject_id, type_query, version, connector, user_id=None):
        return self._not_implemented("performance_analysis")

    def motivation_analysis(self, subject_id, type_query, version, connector, user_id=None):
        return self._not_implemented("motivation_analysis")

    def pedagogic_analysis(self, subject_id, type_query, version, connector, user_id=None):
        return self._not_implemented("pedagogic_analysis")

    def cognitive_analysis(self, subject_id, type_query, version, connector, user_id=None):
        return self._not_implemented("cognitive_analysis")

    def give_up_analysis(self, subject_id, type_query, version, connector, user_id=None):
        return self._not_implemented("give_up_analysis")

    def indicators_analysis(self, subject_id, type_query, version, connector, user_id=None):
        return self._not_implemented("indicators_analysis")