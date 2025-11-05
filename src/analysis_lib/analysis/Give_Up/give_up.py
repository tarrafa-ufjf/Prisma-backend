import pandas as pd
from ..indicator import Indicator
from sqlalchemy import MetaData, Table, select
from database import DatabaseAdmin

class Give_Up(Indicator):
    def __init__(self, mapper):
        self.mapper = mapper

    def student_analysis(self, subject_id, student_id, version, connector):
        df_course = self.course_analysis(subject_id, version, connector)

        df_course["user_id"] = pd.to_numeric(df_course["user_id"], errors="coerce")
        sid = pd.to_numeric(student_id, errors="coerce")

        student_df = df_course.loc[df_course["user_id"] == sid]
        if student_df.empty:
            return None 

        row = student_df.iloc[0]
        row = row.where(pd.notna(row), None).to_dict()
        return row
    
    def course_analysis(self, subject_id, version, connector):
        """
        Analisa 'give-up' por aluno:
        - Retorna os labels de cada classe (engagement/motivation/performance/cognitive)
        - Retorna a flag give_up=True se todos os labels forem 'baixo' ou 'muito_baixo'
        """
        from ..Cognitivo.cognitive import Cognitive
        from ..Engajamento.engagement import Engagement
        from ..Desempenho.performance import Performance
        from ..Motivacao.motivation import Motivation

        cognitive = Cognitive(self.mapper)
        engagement = Engagement(self.mapper)
        performance = Performance(self.mapper)
        motivation = Motivation(self.mapper)

        df_cognitive   = cognitive.course_analysis(subject_id, version, connector)
        df_engagement  = engagement.course_analysis(subject_id, version, connector)
        df_performance = performance.course_analysis(subject_id, version, connector)
        df_motivation  = motivation.course_analysis(subject_id, version, connector)

        dfs = [df_cognitive, df_engagement, df_performance, df_motivation]
        dfs = [df for df in dfs if isinstance(df, pd.DataFrame) and not df.empty]
        if not dfs:
            return pd.DataFrame(columns=[
                "user_id", "full_name",
                "engagement_label", "motivation_label", "performance_label", "cognitive_label",
                "give_up"
            ])

        out = df_cognitive.loc[:, ["user_id", "full_name", "label"]].rename(columns={"label": "cognitive_label"})

        def safe_merge(df_base, df_new, label_col, new_name):
            if not isinstance(df_new, pd.DataFrame) or df_new.empty or (label_col not in df_new.columns):
                df_base[new_name] = pd.NA
                return df_base
            return df_base.merge(
                df_new.loc[:, ["user_id", label_col]].rename(columns={label_col: new_name}),
                on="user_id", how="left"
            )

        out = safe_merge(out, df_engagement,  "posts_required_label",  "engagement_label")
        out = safe_merge(out, df_motivation,  "posts_unrequired_label","motivation_label")
        out = safe_merge(out, df_performance, "performance_label",     "performance_label")

        # Normalização só para a regra do give_up (sem perder o valor original nas colunas *_label)
        def is_low(x: object) -> bool:
            s = (str(x).strip().lower() if pd.notna(x) else "")
            return s in {"muito_baixo", "baixo"}

        label_cols = ["engagement_label", "motivation_label", "performance_label", "cognitive_label"]
        for c in label_cols:
            if c not in out.columns:
                out[c] = pd.NA
            out[c] = out[c].fillna("desconhecido").astype(str)

        out["give_up"] = out[label_cols].apply(lambda row: all(is_low(v) for v in row), axis=1)

        return out[[
            "user_id", "full_name",
            "engagement_label", "motivation_label", "performance_label", "cognitive_label",
            "give_up"
        ]]