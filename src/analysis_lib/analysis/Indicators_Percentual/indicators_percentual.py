import pandas as pd
from ..indicator import Indicator
from sqlalchemy import MetaData, Table, select
from database import DatabaseAdmin

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
        responded_pct = self._calc_pedagogic_responded_percentage(counts_pedagogical)

        return {
            "subject": {
                "id": int(subject_id),
                "good_percentage_engagement": perc_high_engagement,
                "good_percentage_motivation": perc_high_motivation,
                "good_percentage_performance": perc_high_performance,
                "good_percentage_pedagogical": responded_pct,
                "good_percentage_cognitive": 0,
                "percentage_give_up": 0
            }
        }

    def _fetch_engagement_counts(self, subject_id: int, institution_id: int = 1) -> dict:
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        engajamento_global = Table("engajamento_global", metadata, autoload_with=engine)

        with engine.connect() as conn:
            q = (
                select(
                    engajamento_global.c.muito_baixo,
                    engajamento_global.c.baixo,
                    engajamento_global.c.medio,
                    engajamento_global.c.alto,
                    engajamento_global.c.muito_alto,
                )
                .where(engajamento_global.c.institution_id == institution_id)
                .where(engajamento_global.c.subject_id == int(subject_id))
            )
            row = conn.execute(q).mappings().fetchone()

        if not row:
            return {"muito_baixo": 0, "baixo": 0, "medio": 0, "alto": 0, "muito_alto": 0}

        return {
            "muito_baixo": int(row["muito_baixo"] or 0),
            "baixo": int(row["baixo"] or 0),
            "medio": int(row["medio"] or 0),
            "alto": int(row["alto"] or 0),
            "muito_alto": int(row["muito_alto"] or 0),
        }
    
    def _fetch_motivation_counts(self, subject_id: int, institution_id: int = 1) -> dict:
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        motivation_global = Table("motivation_global", metadata, autoload_with=engine)

        with engine.connect() as conn:
            q = (
                select(
                    motivation_global.c.muito_baixo,
                    motivation_global.c.baixo,
                    motivation_global.c.medio,
                    motivation_global.c.alto,
                    motivation_global.c.muito_alto,
                )
                .where(motivation_global.c.institution_id == institution_id)
                .where(motivation_global.c.subject_id == int(subject_id))
            )
            row = conn.execute(q).mappings().fetchone()

        if not row:
            return {"muito_baixo": 0, "baixo": 0, "medio": 0, "alto": 0, "muito_alto": 0}

        return {
            "muito_baixo": int(row["muito_baixo"] or 0),
            "baixo": int(row["baixo"] or 0),
            "medio": int(row["medio"] or 0),
            "alto": int(row["alto"] or 0),
            "muito_alto": int(row["muito_alto"] or 0),
        }
    
    def _fetch_performance_counts(self, subject_id: int, institution_id: int = 1) -> dict:
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        performance_global = Table("performance_global", metadata, autoload_with=engine)

        with engine.connect() as conn:
            q = (
                select(
                    performance_global.c.muito_baixo,
                    performance_global.c.baixo,
                    performance_global.c.medio,
                    performance_global.c.alto,
                    performance_global.c.muito_alto,
                )
                .where(performance_global.c.institution_id == institution_id)
                .where(performance_global.c.subject_id == int(subject_id))
            )
            row = conn.execute(q).mappings().fetchone()

        if not row:
            return {"muito_baixo": 0, "baixo": 0, "medio": 0, "alto": 0, "muito_alto": 0}

        return {
            "muito_baixo": int(row["muito_baixo"] or 0),
            "baixo": int(row["baixo"] or 0),
            "medio": int(row["medio"] or 0),
            "alto": int(row["alto"] or 0),
            "muito_alto": int(row["muito_alto"] or 0),
        }
    
    def _fetch_pedagogic_counts(self, subject_id: int, institution_id: int = 1) -> dict:
        """
        Lê do Postgres local as CONTAGENS por classe pedagógica para a turma.
        Colunas: rapida, normal, atrasada, sem_resposta.
        """
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        pedagogico_global = Table("pedagogico_global", metadata, autoload_with=engine)

        with engine.connect() as conn:
            q = (
                select(
                    pedagogico_global.c.rapida,
                    pedagogico_global.c.normal,
                    pedagogico_global.c.atrasada,
                    pedagogico_global.c.sem_resposta,
                )
                .where(pedagogico_global.c.institution_id == institution_id)
                .where(pedagogico_global.c.subject_id == int(subject_id))
            )
            row = conn.execute(q).mappings().fetchone()

        if not row:
            return {"rapida": 0, "normal": 0, "atrasada": 0, "sem_resposta": 0}

        return {
            "rapida": int(row["rapida"] or 0),
            "normal": int(row["normal"] or 0),
            "atrasada": int(row["atrasada"] or 0),
            "sem_resposta": int(row["sem_resposta"] or 0),
        }

    @staticmethod
    def _calc_high_percentage(counts: dict) -> float:
        """
        Calcula o percentual de 'alto ou mais' = (alto + muito_alto) / total * 100.
        """
        total = (counts.get("muito_baixo", 0) + counts.get("baixo", 0) + counts.get("medio", 0) + counts.get("alto", 0) + counts.get("muito_alto", 0))
        if total == 0:
            return 0.0
        value = (counts.get("alto", 0) + counts.get("muito_alto", 0)) / total * 100.0
        return round(value, 2)
    
    @staticmethod
    def _calc_pedagogic_percentages(counts: dict) -> dict:
        """
        Calcula percentuais por classe: rapida_pct, normal_pct, atrasada_pct, sem_resposta_pct
        E agregados úteis:
        - respondida_pct = (rapida+normal+atrasada)/total
        - em_tempo_pct  = (rapida+normal)/total
        """
        total = (
            counts.get("rapida", 0)
            + counts.get("normal", 0)
            + counts.get("atrasada", 0)
            + counts.get("sem_resposta", 0)
        )
        if total == 0:
            return {
                "rapida_pct": 0.0,
                "normal_pct": 0.0,
                "atrasada_pct": 0.0,
                "sem_resposta_pct": 0.0,
                "respondida_pct": 0.0,
                "em_tempo_pct": 0.0,
                "total": 0,
            }

        def pct(v): 
            return round(100.0 * v / total, 2)

        rapida = counts.get("rapida", 0)
        normal = counts.get("normal", 0)
        atrasada = counts.get("atrasada", 0)
        sem_resp = counts.get("sem_resposta", 0)

        return {
            "rapida_pct": pct(rapida),
            "normal_pct": pct(normal),
            "atrasada_pct": pct(atrasada),
            "sem_resposta_pct": pct(sem_resp),
            "respondida_pct": pct(rapida + normal + atrasada),
            "em_tempo_pct": pct(rapida + normal),
            "total": int(total),
        }
    
    @staticmethod
    def _calc_pedagogic_responded_percentage(counts: dict) -> float:
        """(rápida + normal + atrasada) / total * 100, arredondado a 2 casas."""
        rapida = counts.get("rapida", 0)
        normal = counts.get("normal", 0)
        atrasada = counts.get("atrasada", 0)
        sem_resposta = counts.get("sem_resposta", 0)

        total = rapida + normal + atrasada + sem_resposta
        if total == 0:
            return 0.0
        value = (rapida + normal + atrasada) / total * 100.0
        return round(value, 2)
