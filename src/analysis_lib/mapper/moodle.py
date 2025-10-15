class Moodle:
    def __init__(self, connector):
        self.connector = connector
    
    def general_indicators(self):
        cursor = self.connector.cursor()
        cursor.execute(f'''
            SELECT *
            FROM mdl_course
        ''')
        result = cursor.fetchall() # dict(cursor.fetchall())
        cursor.close()
        return result