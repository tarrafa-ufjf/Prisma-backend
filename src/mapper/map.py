'''
Neste arquivo, devemos criar a lógica do mapeamento das consultas.
'''
class Mapper:
    def __init__(self):
        pass

    def get_moodle_version(connector):
        cursor = connector.cursor()
        cursor.execute(f"""
            SELECT name, value
            FROM mdl_config
            WHERE name = 'release'
        """)
        result = dict(cursor.fetchall())
        cursor.close()
        connector.close()
        return result
