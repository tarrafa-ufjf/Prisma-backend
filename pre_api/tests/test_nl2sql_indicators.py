import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PRE_API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PRE_API_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PRE_API_DIR) not in sys.path:
    sys.path.insert(0, str(PRE_API_DIR))


class NL2SQLIndicatorsDbUriTest(unittest.TestCase):
    def test_uses_configured_nl2sql_db_uri(self):
        from services.nl2sql.db import build_indicators_db_uri

        with patch.dict(os.environ, {"NL2SQL_DB_URI": "postgresql+psycopg://custom"}, clear=True):
            self.assertEqual(build_indicators_db_uri(), "postgresql+psycopg://custom")

    def test_builds_postgres_uri_from_db_env(self):
        from services.nl2sql.db import build_indicators_db_uri

        env = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_USER": "tarrafa",
            "DB_PASSWORD": "senha com espaco",
            "DB_DATABASE": "tarrafa_db",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(
                build_indicators_db_uri(),
                "postgresql+psycopg://tarrafa:senha+com+espaco@localhost:5432/tarrafa_db",
            )

    def test_requires_db_env_values(self):
        from services.nl2sql.db import build_indicators_db_uri

        with patch.dict(os.environ, {"DB_HOST": "localhost"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DB_DATABASE"):
                build_indicators_db_uri()


class NL2SQLIndicatorsConfigTest(unittest.TestCase):
    def test_default_sql_dialect_is_postgres(self):
        original_getenv = os.getenv

        def getenv_without_dialect(name, default=None):
            if name == "NL2SQL_DIALECT":
                return default
            return original_getenv(name, default)

        with patch("os.getenv", side_effect=getenv_without_dialect):
            import services.nl2sql.config as config

            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.SQL_DIALECT, "postgres")


class IndicatorsNL2SQLToolTest(unittest.TestCase):
    def test_forbidden_table_references_are_detected(self):
        from services.nl2sql.tool import referenced_forbidden_tables

        self.assertEqual(
            referenced_forbidden_tables('SELECT * FROM "user" JOIN configs ON true'),
            {"configs", "user"},
        )
        self.assertEqual(
            referenced_forbidden_tables("SELECT * FROM local_indicators_students"),
            set(),
        )

    def test_execute_sql_blocks_forbidden_tables_before_database_access(self):
        from services.nl2sql.tool import IndicatorsNL2SQLTool

        with patch.object(IndicatorsNL2SQLTool, "model_post_init", lambda self, ctx: None):
            tool = IndicatorsNL2SQLTool(db_uri="postgresql+psycopg://u:p@localhost:5432/db")

        with patch("crewai_tools.NL2SQLTool.execute_sql") as execute_sql:
            with self.assertRaisesRegex(ValueError, "configs"):
                tool.execute_sql("SELECT * FROM configs")

        execute_sql.assert_not_called()

    def test_available_tables_query_excludes_forbidden_tables(self):
        from services.nl2sql.tool import IndicatorsNL2SQLTool

        with patch.object(IndicatorsNL2SQLTool, "model_post_init", lambda self, ctx: None):
            tool = IndicatorsNL2SQLTool(db_uri="postgresql+psycopg://u:p@localhost:5432/db")

        with patch.object(IndicatorsNL2SQLTool, "execute_sql", return_value=[]) as execute_sql:
            self.assertEqual(tool._fetch_available_tables(), [])

        query = execute_sql.call_args.args[0]
        self.assertIn("table_schema = 'public'", query)
        self.assertIn("configs", query)
        self.assertIn("roles_users", query)
        self.assertIn("user", query)

    def test_forbidden_columns_are_not_returned(self):
        from services.nl2sql.tool import IndicatorsNL2SQLTool

        with patch.object(IndicatorsNL2SQLTool, "model_post_init", lambda self, ctx: None):
            tool = IndicatorsNL2SQLTool(db_uri="postgresql+psycopg://u:p@localhost:5432/db")

        self.assertEqual(tool._fetch_all_available_columns("configs"), [])


class NL2SQLIndicatorsPromptTest(unittest.TestCase):
    def test_prompt_documents_indicator_columns_and_known_values(self):
        from services.nl2sql.prompts import INDICATORS_RULES

        expected_fragments = [
            "local_indicators_students",
            "global_indicators_tutors",
            "Não há full_name nesta tabela",
            "muito_baixo, baixo, medio, alto, muito_alto",
            "Muito baixo, Baixo, Médio, Alto, Muito alto",
            "label_give_up aparece como texto true/false",
            "engagement, motivation, performance, cognitive, pedagogic",
            "last_status pode ser running, success ou failed",
        ]

        for fragment in expected_fragments:
            self.assertIn(fragment, INDICATORS_RULES)

    def test_final_answer_prompt_uses_original_question_for_language(self):
        from services.nl2sql.answer import build_final_answer_prompt

        prompt = build_final_answer_prompt(
            user_question="Qual é a média de desempenho por subject_id?",
            original_question="What is the average performance by subject?",
            winner_sql="SELECT subject_id, AVG(mean_grade_performance) FROM global_indicators_students GROUP BY subject_id",
            final_json=[{"subject_id": 1, "average": 82}],
        )

        self.assertIn("What is the average performance by subject?", prompt)
        self.assertIn("Qual é a média de desempenho por subject_id?", prompt)
        self.assertIn("mesmo idioma da pergunta original do usuário", prompt)
        self.assertIn("Se a pergunta original estiver em inglês", prompt)


if __name__ == "__main__":
    unittest.main()
