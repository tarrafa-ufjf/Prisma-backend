import pandas as pd
from ..indicator import Indicator
from sqlalchemy import MetaData, Table, select
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
        responded_pct = self._calc_pedagogic_responded_percentage(counts_pedagogical)

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
                "good_percentage_pedagogical": responded_pct,
                "good_percentage_cognitive": perc_high_cognitive,
                "percentage_give_up": perc_high_give_up
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
    
    def _fetch_cognitive_counts(self, subject_id: int, institution_id: int = 1) -> dict:
        """
        Lê as contagens da tabela 'cognitive_global' (muito_baixo..muito_alto) para a turma.
        """
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        cognitive_global = Table("cognitive_global", metadata, autoload_with=engine)

        with engine.connect() as conn:
            q = (
                select(
                    cognitive_global.c.muito_baixo,
                    cognitive_global.c.baixo,
                    cognitive_global.c.medio,
                    cognitive_global.c.alto,
                    cognitive_global.c.muito_alto,
                )
                .where(cognitive_global.c.institution_id == institution_id)
                .where(cognitive_global.c.subject_id == int(subject_id))
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
    
    def _fetch_give_up_counts(self, subject_id: int, institution_id: int = 1) -> dict:
        """
        Calcula as contagens de give-up por ALUNO (exato):
        give_up = True se (cognitive, engagement, motivation, performance) ∈ {muito_baixo, baixo}.
        Estratégia:
        1) Busca rótulos por aluno de cada dimensão via Analyzer.*
        2) Faz o merge por user_id
        3) Marca give_up por aluno
        4) Conta true/false
        """
        # Conecta para rodar as análises existentes
        db_cfg = self.db_admin.get_db_config_from_database(institution_id)
        connector = self.db_admin.get_connection_with_config(db_cfg)
        try:
            analyzer = Analyzer()
            version = analyzer.get_moodle_version(connector)

            # ---- Coletas por dimensão
            df_cog = analyzer.cognitive_analysis(subject_id, 'course', version, connector)
            if not isinstance(df_cog, pd.DataFrame) or df_cog.empty or ("user_id" not in df_cog.columns) or ("label" not in df_cog.columns):
                df_cog = pd.DataFrame(columns=["user_id", "cognitive_label"])
            else:
                df_cog = df_cog.loc[:, ["user_id", "label"]].rename(columns={"label": "cognitive_label"})

            df_eng = analyzer.engagement_analysis(subject_id, 'course', version, connector)
            if not isinstance(df_eng, pd.DataFrame) or df_eng.empty or ("user_id" not in df_eng.columns) or ("posts_required_label" not in df_eng.columns):
                df_eng = pd.DataFrame(columns=["user_id", "engagement_label"])
            else:
                df_eng = df_eng.loc[:, ["user_id", "posts_required_label"]].rename(columns={"posts_required_label": "engagement_label"})

            df_mot = analyzer.motivation_analysis(subject_id, 'course', version, connector)
            if not isinstance(df_mot, pd.DataFrame) or df_mot.empty or ("user_id" not in df_mot.columns) or ("posts_unrequired_label" not in df_mot.columns):
                df_mot = pd.DataFrame(columns=["user_id", "motivation_label"])
            else:
                df_mot = df_mot.loc[:, ["user_id", "posts_unrequired_label"]].rename(columns={"posts_unrequired_label": "motivation_label"})

            df_perf = analyzer.performance_analysis(subject_id, 'course', version, connector)
            if not isinstance(df_perf, pd.DataFrame) or df_perf.empty or ("user_id" not in df_perf.columns) or ("performance_label" not in df_perf.columns):
                df_perf = pd.DataFrame(columns=["user_id", "performance_label"])
            else:
                df_perf = df_perf.loc[:, ["user_id", "performance_label"]]

            users = pd.Index([])
            for d in [df_cog, df_eng, df_mot, df_perf]:
                if not d.empty:
                    users = users.union(d["user_id"])
            if users.empty:
                return {"true": 0, "false": 0}

            base = pd.DataFrame({"user_id": users})

            for d in [df_cog, df_eng, df_mot, df_perf]:
                if not d.empty:
                    base = base.merge(d, on="user_id", how="left")

            def norm(s): return s.astype(str).str.strip().str.lower()
            for col in ["cognitive_label", "engagement_label", "motivation_label", "performance_label"]:
                if col not in base.columns:
                    base[col] = pd.NA
                base[col] = norm(base[col].fillna(""))

            low_set = {"muito_baixo", "baixo"}
            def is_low(x: str) -> bool: return x in low_set

            base["give_up"] = (
                base["cognitive_label"].apply(is_low)
                & base["engagement_label"].apply(is_low)
                & base["motivation_label"].apply(is_low)
                & base["performance_label"].apply(is_low)
            )

            true_count  = int(base["give_up"].sum())
            false_count = int((~base["give_up"]).sum())

            return {"true": true_count, "false": false_count}

        finally:
            try:
                connector.close()
            except Exception:
                pass

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
        total = (counts.get("rapida", 0) + counts.get("normal", 0) + counts.get("atrasada", 0) + counts.get("sem_resposta", 0))
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
    
    @staticmethod
    def _calc_give_up_high_percentage(counts: dict) -> float:
        """
        Retorna a % de alunos marcados como give_up=True.
        Fórmula: true / (true + false) * 100
        """
        true_v = int(counts.get("true", 0) or 0)
        false_v = int(counts.get("false", 0) or 0)
        total = true_v + false_v
        if total == 0:
            return 0.0
        return round(100.0 * true_v / total, 2)
