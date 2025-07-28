'''
Neste arquivo, devemos criar a lógica do mapeamento das consultas.
'''
import re

class Mapper:
    def __init__(self):
        pass

    def get_real_version(self, old):
        pattern = r'[1-9]\d*\.\d+\.\d+'
        resultado = re.search(pattern, old)
        if resultado:
            return resultado.group()
        return None

    def get_moodle_version(self, connector):
        cursor = connector.cursor()
        cursor.execute(f"""
            SELECT name, value
            FROM mdl_config
            WHERE name = 'release'
        """)
        result = cursor.fetchall() # dict(cursor.fetchall())
        cursor.close()
        connector.close()

        version = result[0]['value']
        version = self.get_real_version(version)

        return version
