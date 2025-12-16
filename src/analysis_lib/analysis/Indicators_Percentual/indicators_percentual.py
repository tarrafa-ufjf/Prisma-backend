import pandas as pd
from ..indicator import Indicator
from sqlalchemy import MetaData, Table, select, func
from database import DatabaseAdmin
from src.analysis_lib.analysis.analysis import Analyzer

class Indicators_Percentual(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    def subject_analysis(self, subject_id: int):
        counts_engagement = self._fetch_engagement_counts(subject_id, institution_id=1)
        perc_high_engagement = self._calc_high_percentage(counts_engagement)

        counts_motivation = self._fetch_motivation_counts(subject_id, institution_id=1)
        perc_high_motivation = self._calc_high_percentage(counts_motivation)

        counts_performance = self._fetch_performance_counts(subject_id, institution_id=1)
        perc_high_performance = self._calc_high_percentage(counts_performance)

        counts_pedagogical = self._fetch_pedagogic_counts(subject_id, institution_id=1)
        perc_high_pedagogical = self._calc_high_percentage(counts_pedagogical)

        counts_cognitive = self._fetch_cognitive_counts(subject_id, institution_id=1)
        perc_high_cognitive = self._calc_high_percentage(counts_cognitive)

        counts_give_up = self._fetch_give_up_counts(subject_id, institution_id=1)
        perc_high_give_up = self._calc_give_up_high_percentage(counts_give_up)

        return {
            "subject": {
                "id": int(subject_id),
                "good_percentage_engagement": perc_high_engagement,
                "good_percentage_motivation": perc_high_motivation,
                "good_percentage_performance": perc_high_performance,
                "good_percentage_pedagogical": perc_high_pedagogical,
                "good_percentage_cognitive": perc_high_cognitive,
                "percentage_give_up": perc_high_give_up
            }
        }
        
    def _fetch_label_counts_from_local_indicators_students(self, label_column_name: str, subject_id: int, institution_id: int = 1):
        """
        Lê a tabela local_indicators_students e conta quantos alunos há em cada faixa de valor (muito_baixo, baixo, medio, alto, muito_alto) para o rótulo informado.

        Se não houver NENHUMA linha para a turma, marca como "_not_processed": True.
        """
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        local_indicators_students = Table("local_indicators_students", metadata, autoload_with=engine)

        label_column = getattr(local_indicators_students.c, label_column_name)

        with engine.connect() as conn:
            query = (
                select(
                    label_column.label("label"),
                    func.count().label("count"),
                )
                .where(local_indicators_students.c.institution_id == institution_id)
                .where(local_indicators_students.c.subject_id == int(subject_id))
                .group_by(label_column)
            )
            rows = conn.execute(query).mappings().all()

        # Nenhuma linha encontrada = turma ainda não processada
        if not rows:
            return {"muito_baixo": 0, "baixo": 0, "medio": 0, "alto": 0, "muito_alto": 0, "_not_processed": True}

        counts = {"muito_baixo": 0, "baixo": 0, "medio": 0, "alto": 0, "muito_alto": 0}

        for row in rows:
            raw_label = row["label"]
            label = (raw_label or "").strip().lower()
            if label in counts:
                counts[label] = int(row["count"] or 0)

        return counts

    def _fetch_engagement_counts(self, subject_id: int, institution_id: int = 1):
        return self._fetch_label_counts_from_local_indicators_students(
            label_column_name="label_engagement",
            subject_id=subject_id,
            institution_id=institution_id,
        )
        
    def _fetch_motivation_counts(self, subject_id: int, institution_id: int = 1):
        return self._fetch_label_counts_from_local_indicators_students(
            label_column_name="label_motivation",
            subject_id=subject_id,
            institution_id=institution_id,
        )

    def _fetch_performance_counts(self, subject_id: int, institution_id: int = 1):
        return self._fetch_label_counts_from_local_indicators_students(
            label_column_name="label_performance",
            subject_id=subject_id,
            institution_id=institution_id,
        )
        
    def _fetch_pedagogic_counts(self, subject_id: int, institution_id: int = 1):
        return self._fetch_label_counts_from_local_indicators_students(
            label_column_name="label_relation_teacher_student",
            subject_id=subject_id,
            institution_id=institution_id,
        )
    
    def _fetch_cognitive_counts(self, subject_id: int, institution_id: int = 1):
        return self._fetch_label_counts_from_local_indicators_students(
            label_column_name="label_cognitive",
            subject_id=subject_id,
            institution_id=institution_id,
        )

    def _fetch_give_up_counts(self, subject_id: int, institution_id: int = 1):
        """
        Lê a tabela local_indicators_students e conta quantos alunos da turma estão com label_give_up = true/false.
        """
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        local_indicators_students = Table("local_indicators_students", metadata, autoload_with=engine)

        with engine.connect() as conn:
            query = (
                select(
                    local_indicators_students.c.label_give_up.label("label"),
                    func.count().label("count"),
                )
                .where(local_indicators_students.c.institution_id == institution_id)
                .where(local_indicators_students.c.subject_id == int(subject_id))
                .group_by(local_indicators_students.c.label_give_up)
            )
            rows = conn.execute(query).mappings().all()

        if not rows:
            return {"true": 0, "false": 0, "_not_processed": True}

        counts = {"true": 0, "false": 0}

        for row in rows:
            raw_label = row["label"]
            label = str(raw_label).strip().lower() if raw_label is not None else ""

            if label == "true":
                counts["true"] += int(row["count"] or 0)
            elif label == "false":
                counts["false"] += int(row["count"] or 0)

        return counts

    @staticmethod
    def _calc_high_percentage(counts: dict) -> float:
        """
        Calcula o percentual de 'alto ou mais' = (alto + muito_alto) / total * 100.

        Se a turma ainda não foi processada, retorna -1.0.
        """
        if counts.get("_not_processed", False):
            return -1.0

        total = (counts.get("muito_baixo", 0) + counts.get("baixo", 0) + counts.get("medio", 0) + counts.get("alto", 0) + counts.get("muito_alto", 0))
        if total == 0:
            # Em teoria, se foi processado e há alunos, o total nunca será 0. Se acontecer, tratamos como "sem dado".
            return -1.0

        value = (counts.get("alto", 0) + counts.get("muito_alto", 0)) / total * 100.0
        return round(value, 2)
    
    @staticmethod
    def _calc_give_up_high_percentage(counts: dict) -> float:
        """
        Retorna a % de alunos marcados como give_up=True, através da conta: true / (true + false) * 100

        Se a turma ainda não foi processada, retorna -1.0.
        """
        if counts.get("_not_processed", False):
            return -1.0

        true_v = int(counts.get("true", 0) or 0)
        false_v = int(counts.get("false", 0) or 0)
        total = true_v + false_v
        if total == 0:
            # se não há nenhum aluno com rótulo válido, trata como "sem dado"
            return -1.0

        return round(100.0 * true_v / total, 2)