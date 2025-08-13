import pandas as pd

class Engagement:
    def __init__(self, mapper):
        self.mapper = mapper

    def course_analysis(self, course_id, version, connector):
        data = self.mapper.get_engagement_data(connector, course_id, version)

        # Teste
        return data