import pandas as pd
from ..indicator import Indicator

class Cognitive(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)

    def student_analysis(self, subject_id, student_id, version, connector):
        df_course = self.subject_analysis(subject_id, version, connector)

        df_course["user_id"] = pd.to_numeric(df_course["user_id"], errors="coerce")
        sid = pd.to_numeric(student_id, errors="coerce")

        student_df = df_course.loc[df_course["user_id"] == sid]
        if student_df.empty:
            return None 

        row = student_df.iloc[0]
        row = row.where(pd.notna(row), None).to_dict()
        return row
    
    def subject_analysis(self, subject_id, version, connector):
        all_students = self.mapper.get_all_students(connector, subject_id, version)

        assign_viewed = self.mapper.get_assign_submission_status_viewed(connector, subject_id, version)
        assign_assessable_submitted = self.mapper.get_assign_assessable_submitted(connector, subject_id, version)
        assign_feedback_viewed = self.mapper.get_assign_feedback_viewed(connector, subject_id, version)

        forum_course_viewed = self.mapper.get_course_forum_viewed(connector, subject_id, version)
        forum_post_created = self.mapper.get_forum_post_created(connector, subject_id, version)
        forum_reply_viewed = self.mapper.forum_reply_viewed(connector, subject_id, version)

        quiz_viewed = self.mapper.get_quizz_viewed(connector, subject_id, version)
        quiz_attempt_submitted = self.mapper.get_quizz_attempt_submitted(connector, subject_id, version)
        quiz_attempt_reviewed = self.mapper.get_quizz_attempt_reviewd(connector, subject_id, version)

        '''
            Tratamento dos dados
        '''

        assign_viewed_grouped = (assign_viewed.groupby(['user_id', 'assignment_id'])['timestamp'].count().reset_index(name='count_recorrences'))
        assign_submitted_grouped = (assign_assessable_submitted.groupby(['user_id', 'assignment_id'])['timestamp'].count().reset_index(name='count'))
        assign_feedback_viewed_grouped = (assign_feedback_viewed.groupby(['user_id', 'assignment_id'])['timestamp'].count().reset_index(name='count'))

        forum_course_viewed_grouped = (forum_course_viewed.groupby(['user_id', 'forum_id'])['timestamp'].count().reset_index(name='count'))
        forum_post_created_grouped = (forum_post_created.groupby(['user_id', 'forum_id'])['timestamp'].count().reset_index(name='count'))
        forum_reply_viewed_grouped = (forum_reply_viewed.groupby(['user_id', 'forum_id'])['timestamp'].count().reset_index(name='count'))

        quiz_viewed_grouped = (quiz_viewed.groupby(['user_id', 'quiz_id'])['timestamp'].count().reset_index(name='count'))
        quiz_attempt_submitted_grouped = (quiz_attempt_submitted.groupby(['user_id', 'quiz_id'])['timestamp'].count().reset_index(name='count'))
        quiz_attempt_reviewed_grouped = (quiz_attempt_reviewed.groupby(['user_id', 'quiz_id'])['timestamp'].count().reset_index(name='count'))

        '''
            Confere o nível de profundidade do estudante em cada atividade
        '''

        def df_exists_var(df):
            return isinstance(df, pd.DataFrame) and (not df.empty)

        def to_unique_pairs(df, keys):
            if not df_exists_var(df):
                return set()
            return set(map(tuple, df[keys].drop_duplicates().values))

        def build_levels_for_module(view_pairs, submit_pairs=None, review_pairs=None, max_level=3):
            all_pairs = set()
            if view_pairs:   all_pairs |= view_pairs
            if submit_pairs: all_pairs |= submit_pairs
            if review_pairs: all_pairs |= review_pairs

            levels = {}
            for pair in all_pairs:
                level = 0
                if view_pairs and (pair in view_pairs):
                    level = 1
                if submit_pairs and (pair in submit_pairs):
                    level = 2
                if review_pairs and (pair in review_pairs):
                    level = 3
                levels[pair] = min(level, max_level)

            return levels

        def levels_dict_to_df(levels_dict, user_col, item_col, module_name, potential):
            rows = []
            for (u, item), lvl in levels_dict.items():
                prop = 0.0 if lvl == 0 else (lvl / potential)
                value = 2*prop - 1.0  # escala -1..1
                rows.append({
                    "user_id": u,
                    "item_id": item,           
                    "module": module_name,
                    "level": lvl,
                    "potential": potential,
                    "proportion": prop,
                    "value": value
                })
            return pd.DataFrame(rows)

        def dynamic_potential(view_pairs, submit_pairs, review_pairs):
            if review_pairs and len(review_pairs) > 0:
                return 3
            if submit_pairs and len(submit_pairs) > 0:
                return 2
            if view_pairs and len(view_pairs) > 0:
                return 1
            return 0

        # --------------------------
        # 1) ASSIGN
        # --------------------------
        assign_view_pairs   = to_unique_pairs(assign_viewed_grouped, ["user_id", "assignment_id"])        if df_exists_var(assign_viewed_grouped)           else set()
        assign_submit_pairs = to_unique_pairs(assign_submitted_grouped, ["user_id", "assignment_id"])     if df_exists_var(assign_submitted_grouped)         else set()
        assign_review_pairs = to_unique_pairs(assign_feedback_viewed_grouped, ["user_id", "assignment_id"]) if df_exists_var(assign_feedback_viewed_grouped)   else set()

        assign_potential = dynamic_potential(assign_view_pairs, assign_submit_pairs, assign_review_pairs)
        assign_levels    = build_levels_for_module(assign_view_pairs, assign_submit_pairs, assign_review_pairs, max_level=assign_potential or 0)
        assign_df        = levels_dict_to_df(assign_levels, "user_id", "assignment_id", "assign", assign_potential)

        # --------------------------
        # 2) QUIZ
        # --------------------------
        quiz_view_pairs   = to_unique_pairs(quiz_viewed_grouped, ["user_id", "quiz_id"])                   if df_exists_var(quiz_viewed_grouped)              else set()
        quiz_submit_pairs = to_unique_pairs(quiz_attempt_submitted_grouped, ["user_id", "quiz_id"])        if df_exists_var(quiz_attempt_submitted_grouped)    else set()
        quiz_review_pairs = to_unique_pairs(quiz_attempt_reviewed_grouped, ["user_id", "quiz_id"])         if df_exists_var(quiz_attempt_reviewed_grouped)     else set()

        quiz_potential = dynamic_potential(quiz_view_pairs, quiz_submit_pairs, quiz_review_pairs)
        quiz_levels    = build_levels_for_module(quiz_view_pairs, quiz_submit_pairs, quiz_review_pairs, max_level=quiz_potential or 0)
        quiz_df        = levels_dict_to_df(quiz_levels, "user_id", "quiz_id", "quiz", quiz_potential)

        # --------------------------
        # 3) FORUM
        # --------------------------
        forum_view_pairs    = to_unique_pairs(forum_course_viewed_grouped, ["user_id", "forum_id"])        if df_exists_var(forum_course_viewed_grouped)       else set()
        forum_post_pairs    = to_unique_pairs(forum_post_created_grouped, ["user_id", "forum_id"])         if df_exists_var(forum_post_created_grouped)         else set()
        forum_review_pairs  = to_unique_pairs(forum_reply_viewed_grouped, ["user_id", "forum_id"])         if df_exists_var(forum_reply_viewed_grouped)         else set()

        forum_potential = dynamic_potential(forum_view_pairs, forum_post_pairs, forum_review_pairs)
        forum_levels    = build_levels_for_module(forum_view_pairs, forum_post_pairs, forum_review_pairs, max_level=forum_potential or 0)
        forum_df        = levels_dict_to_df(forum_levels, "user_id", "forum_id", "forum", forum_potential)

        # --------------------------
        # 4) Conciliar tudo
        # --------------------------
        frames = [df for df in [assign_df, quiz_df, forum_df] if df_exists_var(df)]

        if frames:
            per_item = pd.concat(frames, ignore_index=True)

            per_user = (per_item.groupby("user_id", as_index=False)["value"].mean().rename(columns={"value": "cognitive_depth_mean"}))

            # Média por tipo de módulo (forum, quiz, assign)
            per_user_module = (
                per_item.groupby(["user_id", "module"], as_index=False)["level"]
                .mean()
                .pivot(index="user_id", columns="module", values="level")
            )

            for col in ["forum", "quiz", "assign"]:
                if col not in per_user_module.columns:
                    per_user_module[col] = 0

            per_user_module = (
                per_user_module
                .reset_index()
                .rename(columns={
                    "forum": "forum_mean_level",
                    "quiz": "quiz_mean_level",
                    "assign": "assign_mean_level"
                })
                .fillna(0)
                .round(2)
            )
        else:
            per_user = pd.DataFrame(columns=["user_id", "cognitive_depth_mean"])
            per_user_module = pd.DataFrame(columns=[
                "user_id", "forum_mean_level", "quiz_mean_level", "assign_mean_level"
            ]).round(2)

        out = all_students.merge(per_user, on="user_id", how="left")
        out["cognitive_depth_mean"] = out["cognitive_depth_mean"].astype(float).fillna(-1.0)

        out = out.merge(per_user_module, on="user_id", how="left")
        num_cols = ["forum_mean_level", "quiz_mean_level", "assign_mean_level"]
        out[num_cols] = out[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

        cognitive_label = self.discretize_student_levels_class(out)
        out = out.merge(cognitive_label, on="user_id", how="left")

        out["subject_id"] = subject_id

        return out[["subject_id", "user_id", "full_name", "label", "forum_mean_level", "quiz_mean_level", "assign_mean_level"]]

    def discretize_student_levels_class(self, df):
        if df is None or df.empty or "cognitive_depth_mean" not in df.columns:
            return pd.DataFrame(columns=["user_id", "label"])

        serie_real = df.loc[df["cognitive_depth_mean"] > -1, "cognitive_depth_mean"]
        if serie_real.empty:
            out = df[["user_id"]].copy()
            out["label"] = "muito_baixo"
            return out

        q1  = float(serie_real.quantile(0.25))
        q3  = float(serie_real.quantile(0.75))
        iqr = q3 - q1
        lim_inf = q1 - 1.5 * iqr
        lim_sup = q3 + 1.5 * iqr

        def bucket_quantis(x: float) -> str:
            if x <= lim_inf:   return "muito_baixo"
            elif x <= q1:      return "baixo"
            elif x <= q3:      return "medio"
            elif x <= lim_sup: return "alto"
            else:              return "muito_alto"

        out = df[["user_id", "cognitive_depth_mean"]].copy()

        if iqr == 0:
            # fallback quando todos têm o mesmo valor (evita jogar todo mundo no topo)
            # cortes simétricos em [-1, 1]
            bins   = [-1.01, -0.6, -0.2, 0.2, 0.6, 1.01]
            labels = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]
            out["label"] = pd.cut(out["cognitive_depth_mean"], bins=bins,
                                labels=labels, include_lowest=True).astype(str)
        else:
            out["label"] = out["cognitive_depth_mean"].apply(bucket_quantis)

        return out[["user_id", "label"]]