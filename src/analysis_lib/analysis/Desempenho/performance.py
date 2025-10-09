import pandas as pd
import numpy as np
from ..indicator import Indicator

class Performance(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.columns = [
            "user_id",
            "subject_id",
            "muito_baixo",
            "baixo",
            "medio",
            "alto",
            "muito_alto",
        ]
    
    def course_analysis(self, subject_id, version, connector):
        df = self.mapper.get_grades(connector, subject_id, version)
        df_pesos = self.mapper.get_activity_weights(connector, subject_id, version)

        # Converte tipos
        df['performance']  = pd.to_numeric(df['performance'], errors='coerce').fillna(0)
        df['activity_id']  = pd.to_numeric(df['activity_id'], errors='coerce').fillna(0).astype(int)
        df_pesos['grademax']    = pd.to_numeric(df_pesos['grademax'], errors='coerce').fillna(0)
        df_pesos['activity_id'] = pd.to_numeric(df_pesos['activity_id'], errors='coerce').fillna(0).astype(int)

        # Remove atividades 100% zeradas
        atividades_todas_nulas = df.groupby('activity_id', group_keys=False)['performance'].apply(lambda x: (x == 0).all())
        ids_para_remover = atividades_todas_nulas[atividades_todas_nulas].index.tolist()
        df = df[~df['activity_id'].isin(ids_para_remover)]

        # Merge
        df_merged = df.merge(df_pesos[['activity_id', 'grademax', 'activity_name']], on='activity_id', how='left')

        # Nota real
        df_merged['nota_real'] = df_merged['performance'] * (df_merged['grademax'] / 100)

        # Alunos válidos
        alunos_com_nota = df_merged.groupby('user_id', group_keys=False)['nota_real'].sum()
        total_alunos_validos = int((alunos_com_nota > 0).sum())

        # Participação
        participacao_atividade = (
            df_merged[df_merged['performance'] > 0]
            .groupby('activity_id', group_keys=False)['user_id']
            .nunique()
        )
        atividades_validas_ids = participacao_atividade[participacao_atividade >= 0.3 * total_alunos_validos].index

        df_merged = df_merged[df_merged['activity_id'].isin(atividades_validas_ids)]
        df_pesos_filtrado = df_pesos[df_pesos['activity_id'].isin(atividades_validas_ids)]

        # Nota final e max
        notas_finais = df_merged.groupby(['user_id', 'firstname'], group_keys=False)['nota_real'].sum().reset_index()
        notas_finais.rename(columns={'nota_real': 'nota_final'}, inplace=True)

        df_pesos_filtrado = df_pesos_filtrado.copy()
        df_pesos_filtrado['grademax'] = pd.to_numeric(df_pesos_filtrado['grademax'], errors='coerce').fillna(0)
        nota_maxima_semestre = float(df_pesos_filtrado['grademax'].sum())

        if nota_maxima_semestre > 0:
            notas_finais['percentual'] = (notas_finais['nota_final'] / nota_maxima_semestre) * 100
        else:
            notas_finais['percentual'] = 0.0

        notas_finais['situacao'] = notas_finais['percentual'].apply(
            lambda x: 'Aprovado' if x >= 69 else ('RI' if x == 0 else 'Reprovado')
        )

        notas_finais['situacao'] = notas_finais['situacao'].astype(str)

        if nota_maxima_semestre <= 60:
            mask = notas_finais['situacao'] != 'RI'
            notas_finais.loc[mask, 'situacao'] = notas_finais.loc[mask, 'situacao'] + ' com ressalva'

        notas_finais['subject_id']  = subject_id
        notas_finais['grademax']   = round(nota_maxima_semestre, 1)
        notas_finais['nota_final'] = notas_finais['nota_final'].round(1)
        notas_finais['percentual'] = notas_finais['percentual'].round(0)

        return notas_finais
    
    def normalized_grades(self, subject_id, version, connector):
        df_norm = self.course_analysis(subject_id, version, connector)
        df_norm['nota_final'] = pd.to_numeric(df_norm['nota_final'], errors='coerce')
        df_norm['grademax'] = pd.to_numeric(df_norm['grademax'], errors='coerce')

        # Adiciona coluna de nota normalizada (0 a 1)
        df_norm['nota_normalizada'] = df_norm['nota_final'] / df_norm['grademax']

        df_norm['aprovado'] = df_norm['situacao'].str.contains('Aprovado', case=False)
        df_norm['reprovado'] = df_norm['situacao'].str.contains('Reprovado', case=False)
        df_norm['ri'] = df_norm['situacao'] == 'RI'
        df_norm['ressalva'] = df_norm['situacao'].str.contains('ressalva', case=False)

        df_norm_aluno = df_norm.groupby(['user_id', 'firstname']).agg(
            media_nota_normalizada=('nota_normalizada', 'mean'),
            media_percentual=('percentual', 'mean'),
            qtd_cursos=('subject_id', 'nunique'),
            qtd_aprovado=('aprovado', 'sum'),
            qtd_reprovado=('reprovado', 'sum'),
            qtd_ri=('ri', 'sum'),
            qtd_ressalva=('ressalva', 'sum')
        ).reset_index()

        return df_norm_aluno
    
    def discretized_performance(self, subject_id, version, connector):
        df_norm = self.normalized_grades(subject_id, version, connector)

        # Calcula quartis e limites
        q1 = df_norm["media_nota_normalizada"].quantile(0.25)
        q3 = df_norm["media_nota_normalizada"].quantile(0.75)
        q2 = df_norm["media_nota_normalizada"].quantile(0.5)

        iqr = q3 - q1
        lim_inf = q1 - 1.5 * iqr
        lim_sup = q3 + 1.5 * iqr

        # Funções auxiliares
        def discretize_grade(x, lim_inf, q1, q3, lim_sup, method='absolute'):
            if method == 'absolute':
                if x <= 0.2:
                    return 0  
                elif x <= 0.4:
                    return 1  
                elif x <= 0.6:
                    return 2  
                elif x <= 0.8:
                    return 3  
                else:
                    return 4  
            elif method == 'quartis':
                if x <= lim_inf:
                    return 0  
                elif x <= q1:
                    return 1  
                elif x <= q3:
                    return 2  
                elif x <= lim_sup:
                    return 3  
                else:
                    return 4  

        def label_from_mean(mean_value):
            if mean_value == 0:
                return 'muito_baixo'
            elif mean_value == 1:
                return 'baixo'
            elif mean_value == 2:
                return 'medio'
            elif mean_value == 3:
                return 'alto'
            elif mean_value >= 4:
                return 'muito_alto'
            return 'Sem dados'

        # Aplica discretizações numéricas e rotula com média
        performance_labels = []
        for index, row in df_norm.iterrows():
            nota = row["media_nota_normalizada"]
            if pd.notna(nota):
                val_quartis = discretize_grade(nota, lim_inf, q1, q3, lim_sup, method='quartis')
                val_absolute = discretize_grade(nota, 0, 0.4, 0.6, 0.8, method='absolute')
                mean_value = round(np.mean([val_quartis, val_absolute]))
                label = label_from_mean(mean_value)
            else:
                label = "Sem dados"
            performance_labels.append(label)

        # Cria a nova coluna
        df_norm["performance"] = performance_labels
        df_norm["subject_id"] = subject_id

        return df_norm[["user_id", "subject_id", "performance"]]
    
    def general_analysis(self, version, connector, analysis_config):
        batch_size = analysis_config.get("batch_size")
        processed = analysis_config.get("processed", 0)
        engine = self.get_connector()

        # Se total ainda não foi definido, calcular (baseado no banco fonte)
        if analysis_config["total"] == 0:
            df_courses = self.mapper.get_courses(connector, version)  
            df_courses = pd.DataFrame(df_courses, columns=['subject_id'])
            analysis_config["total"] = len(df_courses)

        total = analysis_config["total"]

        # Lista para acumular resultados
        results = []

        # Processar cursos a partir do ponto onde parou
        for i in range(processed + 1, total + 1):
            result = self.discretized_performance(i, version, connector)

            if not result.empty:
                result["subject_id"] = i
                results.append(result)

            analysis_config["processed"] += 1

            self.print_load("Desempenho", analysis_config["processed"], total, 6)

            # Quando atingir batch_size, salvar e retornar
            if analysis_config["processed"] % batch_size == 0 and results:
                df = pd.concat(results, ignore_index=True)
                df["institution_id"] = 1 

                df_counts = (
                    df.groupby(["institution_id", "subject_id", "performance"])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )

                labels = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]
                for lbl in labels:
                    if lbl not in df_counts.columns:
                        df_counts[lbl] = 0

                df_counts.to_sql("performance_global", engine, if_exists="append", index=False)
                results = []  # limpa lista

                return analysis_config

        # Se terminar todos os cursos (salva o que restou)
        if results:
            df = pd.concat(results, ignore_index=True)
            df["institution_id"] = 1 
            df_counts = (
                df.groupby(["institution_id", "subject_id", "performance"])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )

            labels = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]
            for lbl in labels:
                if lbl not in df_counts.columns:
                    df_counts[lbl] = 0

            df_counts.to_sql("performance_global", engine, if_exists="append", index=False)

        return analysis_config
    
    def status_students_analysis(self, version, connector, subject_id=None):
        rows = []
        df = self.course_analysis(subject_id, version, connector)

        s = df["situacao"].astype(str)
        status = np.where(
        s.eq("RI"), "RI",
            np.where(s.str.startswith("Aprovado", na=False), "Aprovado",
                np.where(s.str.startswith("Reprovado", na=False), "Reprovado", "Outro"))
        )

        counts = pd.Series(status).value_counts()
        rows.append({
            "subject_id": subject_id,
            "Aprovado": int(counts.get("Aprovado", 0)),
            "Reprovado": int(counts.get("Reprovado", 0)),
            "RI": int(counts.get("RI", 0)),
        })

        return pd.DataFrame(rows, columns=["subject_id", "Aprovado", "Reprovado", "RI"])
    
    def grades_students_analysis(self, version, connector, subject_id=None):
        return self.course_analysis(subject_id, version, connector)