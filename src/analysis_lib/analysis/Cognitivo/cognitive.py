import pandas as pd
from ..indicator import Indicator

class Cognitive(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
    
    def course_analysis(self, subject_id, version, connector):
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
        if(not assign_feedback_viewed.empty):
            assign_feedback_viewed_grouped = (assign_feedback_viewed.groupby(['user_id', 'assignment_id'])['timestamp'].count().reset_index(name='count'))

        forum_course_viewed_grouped = (forum_course_viewed.groupby(['user_id', 'forum_id'])['timestamp'].count().reset_index(name='count'))
        forum_post_created_grouped = (forum_post_created.groupby(['user_id', 'forum_id'])['timestamp'].count().reset_index(name='count'))
        forum_reply_viewed_grouped = (forum_reply_viewed.groupby(['user_id', 'original_post_id'])['timestamp'].count().reset_index(name='count'))

        quiz_viewed_grouped = (quiz_viewed.groupby(['user_id', 'quiz_id'])['timestamp'].count().reset_index(name='count'))
        quiz_attempt_submitted_grouped = (quiz_attempt_submitted.groupby(['user_id', 'quiz_id'])['timestamp'].count().reset_index(name='count'))
        quiz_attempt_reviewed_grouped = (quiz_attempt_reviewed.groupby(['user_id', 'quiz_id'])['timestamp'].count().reset_index(name='count'))

        '''
            Confere o nível de profundidade do estudante em cada atividade
        '''

        def df_exists(df_name: str) -> bool:
            # verifica se a variável existe no escopo global
            if df_name not in globals():
                return False
            df = globals()[df_name]
            # verifica se é um DataFrame e se não está vazio
            return hasattr(df, "empty") and df is not None and not df.empty
        
        # -----------------------------
        # 1) ASSIGN
        # nível 1 = visualizou; nível 2 = submeteu; nível 3 = viu feedback
        # -----------------------------
        assign_lvl1_users = set()
        assign_lvl2_users = set()
        assign_lvl3_users = set()

        if df_exists("assign_viewed_grouped"):
            # pega todos os user_id presentes no DF de "visualizações" de assign
            assign_lvl1_users = set(assign_viewed_grouped["user_id"].unique())

        if df_exists("assign_submitted_grouped"):
            # pega todos os user_id presentes no DF de "submissões" de assign
            assign_lvl2_users = set(assign_submitted_grouped["user_id"].unique())

        if df_exists("assign_feedback_viewed_grouped"):
            # pega todos os user_id presentes no DF de "feedback visto" de assign
            assign_lvl3_users = set(assign_feedback_viewed_grouped["user_id"].unique())

        # Agora calculamos o nível máximo do usuário em ASSIGN
        assign_levels = {}  # user_id -> nível
        all_assign_users = assign_lvl1_users | assign_lvl2_users | assign_lvl3_users

        for user in all_assign_users:
            # começa do nível 0
            level = 0

            # se visualizou, pelo menos nível 1
            if user in assign_lvl1_users:
                level = 1

            # se submeteu, sobe para nível 2
            if user in assign_lvl2_users:
                level = 2

            # se viu feedback, sobe para nível 3
            if user in assign_lvl3_users:
                level = 3

            assign_levels[user] = level

        # -----------------------------
        # 2) FORUM
        # nível 1 = viu fórum; nível 2 = criou post; nível 3 = viu reply ao próprio post
        # -----------------------------
        forum_lvl1_users = set()
        forum_lvl2_users = set()
        forum_lvl3_users = set()

        if df_exists("forum_course_viewed_grouped"):
            forum_lvl1_users = set(forum_course_viewed_grouped["user_id"].unique())

        if df_exists("forum_post_created_grouped"):
            forum_lvl2_users = set(forum_post_created_grouped["user_id"].unique())

        if df_exists("forum_reply_viewed_grouped"):
            forum_lvl3_users = set(forum_reply_viewed_grouped["user_id"].unique())

        forum_levels = {}
        all_forum_users = forum_lvl1_users | forum_lvl2_users | forum_lvl3_users

        for user in all_forum_users:
            level = 0
            if user in forum_lvl1_users:
                level = 1
            if user in forum_lvl2_users:
                level = 2
            if user in forum_lvl3_users:
                level = 3
            forum_levels[user] = level

        # -----------------------------
        # 3) QUIZ
        # nível 1 = viu quiz; nível 2 = enviou tentativa; nível 3 = revisou tentativa
        # -----------------------------
        quiz_lvl1_users = set()
        quiz_lvl2_users = set()
        quiz_lvl3_users = set()

        if df_exists("quiz_viewed_grouped"):
            quiz_lvl1_users = set(quiz_viewed_grouped["user_id"].unique())

        if df_exists("quiz_attempt_submitted_grouped"):
            quiz_lvl2_users = set(quiz_attempt_submitted_grouped["user_id"].unique())

        if df_exists("quiz_attempt_reviewed_grouped"):
            quiz_lvl3_users = set(quiz_attempt_reviewed_grouped["user_id"].unique())

        quiz_levels = {}
        all_quiz_users = quiz_lvl1_users | quiz_lvl2_users | quiz_lvl3_users

        for user in all_quiz_users:
            level = 0
            if user in quiz_lvl1_users:
                level = 1
            if user in quiz_lvl2_users:
                level = 2
            if user in quiz_lvl3_users:
                level = 3
            quiz_levels[user] = level
        
        #-----------------------------
        # 4) Compilar todos os alunos com seus níveis
        # -----------------------------
        all_user_ids = all_students['user_id']
        assign_list = [assign_levels.get(uid, 0) for uid in all_user_ids]
        forum_list  = [forum_levels.get(uid, 0)  for uid in all_user_ids]
        quiz_list   = [quiz_levels.get(uid, 0)   for uid in all_user_ids]

        all_students_with_activities = all_students.copy()
        all_students_with_activities['assign_level'] = assign_list
        all_students_with_activities['forum_level']  = forum_list
        all_students_with_activities['quiz_level']   = quiz_list

        return all_students_with_activities
    
    
    '''Implementar análise cognitiva global'''

    def discretize_student_levels_class(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['avg_level'] = df[['assign_level', 'forum_level', 'quiz_level']].mean(axis=1)

        Q1 = df['avg_level'].quantile(0.25)
        Q2 = df['avg_level'].quantile(0.50)
        Q3 = df['avg_level'].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        def categorize(value):
            if value < lower_bound:
                return 'muito_baixo'
            elif value < Q1:
                return 'baixo'
            elif value <= Q3:
                return 'medio'
            elif value <= upper_bound:
                return 'alto'
            else:
                return 'muito_alto'

        df['label'] = df['avg_level'].apply(categorize)

        return df[['user_id', 'label']]


    def general_analysis(self, version, connector, analysis_config):
        batch_size = analysis_config["batch_size"]
        processed = analysis_config["processed"]
        engine = self.get_connector()

        if analysis_config["total"] == 0:
            df_courses = self.mapper.get_courses(connector, version)
            df_courses = pd.DataFrame(df_courses, columns=['subject_id'])
            analysis_config["total"] = len(df_courses)

        total = analysis_config["total"]
        df = pd.DataFrame(columns=['subject_id', 'user_id', 'label'])

        if processed == 0:
            processed = 1

        for i in range(processed + 1, total + 1):
            result = self.course_analysis(i, version, connector)
            result = self.discretize_student_levels_class(result)

            if not result.empty:
                result["subject_id"] = i
                df = pd.concat([df, result], ignore_index=True)
            analysis_config["processed"] += 1

            self.print_load("Cognitivo", analysis_config["processed"], total, 8)

            if analysis_config["processed"] % batch_size == 0:
                df["institution_id"] = 1

                # df.to_sql("cognitive_global", engine, if_exists="append", index=False)
                self.create_user_course_label_df(df)

                self.aggregate_user_results(df, engine)

                return analysis_config

        if not df.empty:
            # df.to_sql("cognitive_global", engine, if_exists="append", index=False)

            self.create_user_course_label_df(df)
            self.aggregate_user_results(df, engine)

        return analysis_config

    
    def create_user_course_label_df(self, result_df: pd.DataFrame) -> pd.DataFrame:
        df = result_df[['user_id', 'subject_id', 'label']].copy()
        df = df.rename(columns={'subject_id': 'course_id'})
        return df


    def aggregate_user_results(self, df: pd.DataFrame, engine) -> pd.DataFrame:
        label_map = {
            'muito_baixo': 0,
            'baixo': 1,
            'medio': 2,
            'alto': 3,
            'muito_alto': 4
        }
        df['label_num'] = df['label'].map(label_map)

        df_user_mean = (
            df.groupby('user_id')['label_num']
            .mean()
            .reset_index()
            .rename(columns={'label_num': 'avg_label_num'})
        )

        def discretize_label(value):
            if value < 0.5:
                return 'muito_baixo'
            elif value < 1.5:
                return 'baixo'
            elif value < 2.5:
                return 'medio'
            elif value < 3.5:
                return 'alto'
            else:
                return 'muito_alto'

        df_user_mean['label_final'] = df_user_mean['avg_label_num'].apply(discretize_label)

        df_merged = df.merge(df_user_mean[['user_id', 'label_final']], on='user_id', how='left')

        df_summary = (
            df_merged.groupby(['subject_id', 'label_final'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        for col in ['muito_baixo', 'baixo', 'medio', 'alto', 'muito_alto']:
            if col not in df_summary.columns:
                df_summary[col] = 0

        df_summary['institution_id'] = 1
        df_summary.to_sql("cognitive_global", engine, if_exists="append", index=False)

        return df_summary