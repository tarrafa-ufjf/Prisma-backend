import pandas as pd
import numpy as np
import math
from ....indicator import Indicator

class Analysis_login(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def tutors_analysis(self, subject_id, student_id, version, connector):
        print("Chegou student")
        return None
    
    def _best_block_dynamic_window(self, df_daily_events, gap_days: int = 21, pct_of_peak: float = 0.02, floor_min: int = 10,):
        """
        - A ideia é ignorar "cauda longa" (acessos anos depois).
        - 1) Agrega logs por dia (df_daily_events já vem assim).
        - 2) Calcula pico_diario = max(events).
        - 3) Define "dia ativo" como: events_dia >= max(floor_min, ceil(pct_of_peak * pico_diario))
             * O pct escala com o tamanho da turma/curso
             * O floor evita que cursos pequenos considerem 1-2 eventos como "dia ativo"
        - 4) Considera apenas dias ativos e agrupa em blocos permitindo gaps <= gap_days.
        - 5) Escolhe o bloco com maior soma de eventos (bloco "principal" do curso).
        """
        if df_daily_events is None or df_daily_events.empty:
            return None, None
        
        daily = df_daily_events.copy()

        if "day" not in daily.columns or "events" not in daily.columns:
            return None, None

        daily["day"] = pd.to_datetime(daily["day"], errors="coerce").dt.normalize()
        daily["events"] = pd.to_numeric(daily["events"], errors="coerce").fillna(0).astype(int)
        daily = daily.dropna(subset=["day"]).sort_values("day").reset_index(drop=True)

        if daily.empty or daily["events"].sum() <= 0:
            return None, None

        peak_daily = int(daily["events"].max())
        active_min_dynamic = max(floor_min, int(math.ceil(pct_of_peak * peak_daily)))

        active_days = daily[daily["events"] >= active_min_dynamic].copy()
        if active_days.empty:
            pos = daily[daily["events"] > 0] # se nada bater o active_min, devolve janela total (dias com evento > 0)
            if pos.empty:
                return None, None
            return pos["day"].iloc[0], pos["day"].iloc[-1]

        active_days = active_days.sort_values("day").reset_index(drop=True)

        # Quebra em blocos quando gap > gap_days
        active_days["prev_day"] = active_days["day"].shift(1)
        active_days["gap"] = (active_days["day"] - active_days["prev_day"]).dt.days
        active_days["new_block"] = active_days["gap"].isna() | (active_days["gap"] > gap_days)
        active_days["block_id"] = active_days["new_block"].cumsum()

        agg = active_days.groupby("block_id").agg(
            start_day=("day", "min"),
            end_day=("day", "max"),
            events_sum=("events", "sum"),
            days=("day", "count"),
        ).reset_index()

        best = agg.sort_values(["events_sum", "days"], ascending=[False, False]).iloc[0]

        start_at = best["start_day"]
        end_at = best["end_day"]
        
        return start_at, end_at
    
    def _discretize_by_quantiles(self, s, labels=("Ruim", "Médio", "Bom", "Ótimo")):
        s = pd.to_numeric(s, errors="coerce").fillna(0)

        # Caso especial: todos iguais
        if s.nunique() <= 1:
            return pd.Series([labels[1]] * len(s), index=s.index)

        try:
            out = pd.qcut(s.rank(method="average"), q=4, labels=labels, duplicates="drop")
            return out.astype(str).replace("nan", labels[1])

        except ValueError:
            n_unique = s.nunique()
            q = min(4, n_unique) 
            try:
                out = pd.qcut(s.rank(method="average"), q=q, labels=labels[:q], duplicates="drop")
                return out.astype(str).replace("nan", labels[1])
            except Exception:
                # Último recurso: percentis manuais
                p25, p50, p75 = np.percentile(s, [25, 50, 75])
                def f(x):
                    if x <= p25: return labels[0]
                    if x <= p50: return labels[1]
                    if x <= p75: return labels[2]
                    return labels[3]
                return s.apply(f)

    def _compute_window_metrics(self, df_events: pd.DataFrame, ts_col: str, start_at: pd.Timestamp, end_at: pd.Timestamp):
        base_cols = ["userid", "total", "weekly"]

        if df_events.empty or start_at is None or end_at is None:
            return pd.DataFrame(columns=base_cols)

        df = df_events.copy()
        df["_day"] = df[ts_col].dt.normalize()
        mask = (df["_day"] >= start_at) & (df["_day"] <= end_at)
        dfw = df.loc[mask].copy()

        if dfw.empty:
            return pd.DataFrame(columns=base_cols)

        window_days = int((end_at - start_at).days) + 1
        window_weeks = max(window_days / 7.0, 1.0)

        out = (
            dfw.groupby("userid")
            .agg(total=("userid", "size"))
            .reset_index()
        )
        out["weekly"] = out["total"] / window_weeks

        return out[base_cols]

    def subject_analysis(self, subject_id, version, connector):
        df_course_views = self.mapper.fetch_tutors_login_subject(connector, version, subject_id)
        all_user_ids = (pd.Series(df_course_views["userid"].unique()).dropna().astype(int))
        df_metrics = pd.DataFrame({"userid": all_user_ids})

        df_course_views["course_view_at"] = pd.to_datetime(df_course_views.get("data_acesso_curso"), errors="coerce")
        df_course_views = df_course_views.sort_values(["userid", "course_view_at"])

        df_course_views_valid = df_course_views.dropna(subset=["course_view_at"]).copy()

        # ===============================
        # JANELA DO CURSO 
        # ===============================
        df_daily_events = self.mapper.fetch_daily_events(connector, version, subject_id)
        start_at, end_at = self._best_block_dynamic_window(df_daily_events=df_daily_events, gap_days=21, pct_of_peak=0.02, floor_min=10)

        # ===============================
        # MÉTRICAS GERAIS 
        # ===============================
        course_metrics = []
        if not df_course_views_valid.empty:
            for tutor_id, group in df_course_views_valid.groupby("userid"):
                group = group.sort_values("course_view_at")
                total_course_views = len(group)

                active_period_days = (group["course_view_at"].max() - group["course_view_at"].min()).days + 1
                weeks = max(active_period_days / 7, 1)
                weekly_course_views = total_course_views / weeks

                course_metrics.append({
                    "userid": int(tutor_id),
                    "total_course_views": int(total_course_views),
                    "weekly_course_views": round(weekly_course_views, 2),
                })

        df_course_metrics = pd.DataFrame(course_metrics, columns=["userid", "total_course_views", "weekly_course_views"])

        # ===============================
        # MÉTRICAS NA JANELA
        # ===============================
        if start_at is not None and end_at is not None:
            start_at = pd.to_datetime(start_at).normalize()
            end_at = pd.to_datetime(end_at).normalize()

            df_view_win = self._compute_window_metrics(
                df_course_views_valid, "course_view_at", start_at, end_at
            ).rename(columns={
                "total": "total_course_views_window",
                "weekly": "weekly_course_views_window"
            })
        else:
            start_at = None
            end_at = None
            df_view_win = pd.DataFrame(columns=["userid", "total_course_views_window", "weekly_course_views_window"])

        # ===============================
        # CONSOLIDAÇÃO
        # ===============================
        df_metrics = df_metrics.merge(df_course_metrics, on="userid", how="left")
        df_metrics = df_metrics.merge(df_view_win, on="userid", how="left")

        df_metrics["total_course_views"] = df_metrics["total_course_views"].fillna(0).astype(int)
        df_metrics["weekly_course_views"] = df_metrics["weekly_course_views"].fillna(0)

        df_metrics["total_course_views_window"] = df_metrics["total_course_views_window"].fillna(0).astype(int)
        df_metrics["weekly_course_views_window"] = df_metrics["weekly_course_views_window"].fillna(0)

        # ===============================
        # DISCRETIZAÇÃO
        # ===============================
        df_metrics["course_view_class_window"] = self._discretize_by_quantiles(df_metrics["weekly_course_views_window"])

        df_metrics.to_csv(f"tutors_{subject_id}.csv", index=False)
        
        return None