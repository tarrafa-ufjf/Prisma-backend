import pandas as pd
import numpy as np
from ..indicator import Indicator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import MetaData, Table

class Pedagogic(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        # pesos para classificação de respostas em fórum
        self.PESO_RAPIDA = 3
        self.PESO_NORMAL = 2
        self.PESO_ATRASADA = 1
        # peso para contar mensagens privadas (cada mensagem vale este peso)
        self.PESO_MENSAGEM = 1

        # combinação entre componente fórum e componente mensagens (0..1)
        # indice_final_sem_acesso = ALPHA * indice_forum + (1-ALPHA) * indice_mensagens
        self.ALPHA = 0.75

        # *** ADIÇÃO ***
        # peso do componente de acesso (0..1). 
        # ACCESS_ALPHA = 0 => não considera acesso; >0 incorpora índice de acesso ao índice final.
        self.ACCESS_ALPHA = 0.10

    def course_analysis(self, course_id, version, connector):
        df_forum = self.mapper.get_forum_data(connector, course_id, version)
        df_forum["autor_resposta_completo"] = df_forum.get("autor_resposta_completo", pd.Series()).fillna("Sem resposta")

        df_msg = self.mapper.get_private_messages(connector, course_id, version)
        df_msg["remetente_completo"] = df_msg.get("remetente_completo", pd.Series()).fillna("Sem tutor")

        df_access = self.mapper.get_tutor_access_frequency(connector, course_id, version)
        df_access["tutor_completo"] = df_access.get("tutor_completo", pd.Series()).fillna("Sem tutor")

        # Converter timestamps
        df_forum["resposta_enviada_em"] = pd.to_datetime(df_forum["resposta_enviada_em"], errors='coerce')
        df_forum["post_criado_em"] = pd.to_datetime(df_forum["post_criado_em"], errors='coerce')
        df_msg["enviada_em"] = pd.to_datetime(df_msg["enviada_em"], errors='coerce')
        df_access["ultimo_acesso"] = pd.to_datetime(df_access["ultimo_acesso"], errors='coerce')

        # Filtrar respostas (existência de resposta_id)
        df_forum_respostas = df_forum.dropna(subset=["resposta_id"]).copy()
        df_msg_respostas = df_msg.dropna(subset=["mensagem_id"]).copy()

        # ===== Primeira resposta por post (fórum) e primeira mensagem por par (tutor->aluno) =====
        if not df_forum_respostas.empty:
            df_forum_primeira = (
                df_forum_respostas.sort_values("resposta_enviada_em")
                .groupby("post_aluno_id", as_index=False)
                .first()
            )
        else:
            df_forum_primeira = pd.DataFrame(columns=df_forum_respostas.columns)

        if not df_msg_respostas.empty:
            df_msg_primeira = (
                df_msg_respostas.sort_values("enviada_em")
                .groupby(["remetente_id", "destinatario_id"], as_index=False)
                .first()
            )
        else:
            df_msg_primeira = pd.DataFrame(columns=df_msg_respostas.columns)
        
        # ===============================
        # Calcular tempo de resposta (horas) e classificar (apenas para fórum)
        # ===============================
        if "resposta_enviada_em" in df_forum_primeira.columns and "post_criado_em" in df_forum_primeira.columns:
            df_forum_primeira["horas"] = (
                df_forum_primeira["resposta_enviada_em"] - df_forum_primeira["post_criado_em"]
            ).dt.total_seconds() / 3600
        else:
            df_forum_primeira["horas"] = np.nan

        def classificar_resposta(horas):
            if pd.isna(horas):
                return 'Sem resposta'
            elif horas <= 24:
                return 'Rápida (≤24h)'
            elif horas > 120:
                return 'Atrasada (>5 dias)'
            else:
                return 'Normal'

        df_forum_primeira["classificacao"] = df_forum_primeira["horas"].apply(classificar_resposta)

        # ===============================
        # Preparar contagens por tutor
        # Vamos criar um resumo por tutor usando tutor_id sempre que possível (mais robusto que usar só nome)
        # ===============================
        # Contagem de respostas (fórum) por tutor_id
        if not df_forum_primeira.empty:
            # aqui df_forum_primeira tem coluna autor_resposta_id
            forum_count = df_forum_primeira.groupby(["autor_resposta_id", "autor_resposta_completo"])["resposta_id"].count().reset_index()
            forum_count.columns = ["tutor_id", "tutor_completo", "total_respostas_forum"]
        else:
            forum_count = pd.DataFrame(columns=["tutor_id", "tutor_completo", "total_respostas_forum"])

        # contagem por classificação
        if not df_forum_primeira.empty:
            class_count = df_forum_primeira.groupby(["autor_resposta_id", "classificacao"])["resposta_id"].count().unstack(fill_value=0).reset_index()
            class_count = class_count.rename(columns={"autor_resposta_id": "tutor_id"})
        else:
            class_count = pd.DataFrame()

        # contagem de mensagens por tutor (remetente_id)
        if not df_msg_respostas.empty:
            msg_count = df_msg_respostas.groupby(["remetente_id", "remetente_completo"])["mensagem_id"].count().reset_index()
            msg_count.columns = ["tutor_id", "tutor_completo_msg", "total_mensagens"]
        else:
            msg_count = pd.DataFrame(columns=["tutor_id", "tutor_completo_msg", "total_mensagens"])

        # Unir as contagens em um DataFrame resumo inicial
        # Começamos com a união (outer) para pegar tutores que aparecem só em forum ou só em mensagens
        df_resumo = pd.merge(forum_count, msg_count, how="outer", on="tutor_id")

        # Ajustar colunas de nome
        df_resumo["tutor_completo"] = df_resumo["tutor_completo"].fillna(df_resumo.get("tutor_completo_msg"))
        df_resumo = df_resumo.drop(columns=["tutor_completo_msg"])

        # preencher NaNs numéricos por zeros
        for col in ["total_respostas_forum", "total_mensagens"]:
            if col not in df_resumo.columns:
                df_resumo[col] = 0
        df_resumo[["total_respostas_forum", "total_mensagens"]] = df_resumo[["total_respostas_forum", "total_mensagens"]].fillna(0).astype(int)

        # unir contagens de classificação se existirem
        if not class_count.empty:
            df_resumo = pd.merge(df_resumo, class_count, how="left", on="tutor_id")
            # garantir colunas de classificacao
            for c in ["Rápida (≤24h)", "Normal", "Atrasada (>5 dias)", "Sem resposta"]:
                if c not in df_resumo.columns:
                    df_resumo[c] = 0
        else:
            # criar colunas vazias
            df_resumo["Rápida (≤24h)"] = 0
            df_resumo["Normal"] = 0
            df_resumo["Atrasada (>5 dias)"] = 0
            df_resumo["Sem resposta"] = 0

        # renomear para campos usados adiante
        df_resumo = df_resumo.rename(columns={
            "Rápida (≤24h)": "respostas_rapidas",
            "Normal": "respostas_normais",
            "Atrasada (>5 dias)": "respostas_atrasadas",
            "Sem resposta": "sem_resposta"
        })

        # ===============================
        # *** ADIÇÃO *** - incorporar dados de acesso (df_access)
        # ===============================
        # df_access tem colunas: tutor_id, tutor_completo, total_events, dias_acesso, ultimo_acesso
        if not df_access.empty:
            # garantir tipos
            df_access["tutor_id"] = df_access["tutor_id"].astype(int)
            # integrar (left merge para manter todos do df_resumo)
            df_resumo = pd.merge(df_resumo, df_access[["tutor_id", "total_events", "dias_acesso", "ultimo_acesso"]], how="left", on="tutor_id")
        else:
            df_resumo["total_events"] = 0
            df_resumo["dias_acesso"] = 0
            df_resumo["ultimo_acesso"] = pd.NaT

        # preencher NaNs
        df_resumo[["total_events", "dias_acesso"]] = df_resumo[["total_events", "dias_acesso"]].fillna(0).astype(int)

        # ===============================
        # Cálculos de índices (fórum, mensagens, acesso) e índice combinado
        # ===============================
        # ===== índice fórum (0..1) baseado em pesos da classificação =====
        df_resumo["score_forum_raw"] = (
            df_resumo["respostas_rapidas"] * self.PESO_RAPIDA
            + df_resumo["respostas_normais"] * self.PESO_NORMAL
            + df_resumo["respostas_atrasadas"] * self.PESO_ATRASADA
        )
        df_resumo["max_score_forum"] = df_resumo["total_respostas_forum"] * self.PESO_RAPIDA
        df_resumo["indice_forum"] = np.where(
            df_resumo["max_score_forum"] > 0,
            df_resumo["score_forum_raw"] / df_resumo["max_score_forum"],
            0.0
        )

        # ===== índice mensagens (0..1): normaliza pelo máximo de mensagens entre tutores =====
        max_msgs = df_resumo["total_mensagens"].max() if df_resumo["total_mensagens"].max() > 0 else 1
        df_resumo["score_msg_raw"] = df_resumo["total_mensagens"] * self.PESO_MENSAGEM
        df_resumo["indice_msg"] = df_resumo["score_msg_raw"] / (max_msgs * self.PESO_MENSAGEM)

        # ===== índice de acesso (0..1) baseado em dias_acesso (regularidade) =====
        max_dias = df_resumo["dias_acesso"].max() if df_resumo["dias_acesso"].max() > 0 else 1
        df_resumo["indice_acesso"] = df_resumo["dias_acesso"] / max_dias

        # ===== índice combinado sem acesso (original) =====
        df_resumo["indice_combinado_sem_acesso"] = self.ALPHA * df_resumo["indice_forum"] + (1 - self.ALPHA) * df_resumo["indice_msg"]

        # ===== índice final incluindo acesso (se ACCESS_ALPHA > 0) =====
        if self.ACCESS_ALPHA > 0:
            df_resumo["indice_combinado"] = (1 - self.ACCESS_ALPHA) * df_resumo["indice_combinado_sem_acesso"] + self.ACCESS_ALPHA * df_resumo["indice_acesso"]
        else:
            df_resumo["indice_combinado"] = df_resumo["indice_combinado_sem_acesso"]

        df_resumo["indice_percent"] = df_resumo["indice_combinado"] * 100

        # ranking
        df_ranking = df_resumo.sort_values("indice_combinado", ascending=False).reset_index(drop=True)
        df_ranking.index = df_ranking.index + 1  # rank starting at 1

        for col in df_ranking.select_dtypes(include=["datetime64[ns]"]).columns:
            df_ranking[col] = df_ranking[col].dt.strftime("%Y-%m-%d %H:%M:%S")


        return df_ranking

    def general_analysis(self, version, connector, analysis_config):
        batch_size = analysis_config["batch_size"]
        processed = analysis_config["processed"]
        engine = self.get_connector()

        # Se total ainda não foi definido, calcular (baseado no banco fonte)
        if analysis_config["total"] == 0:
            df_courses = self.mapper.get_courses(connector, version)  
            df_courses = pd.DataFrame(df_courses, columns=['course_id'])
            analysis_config["total"] = len(df_courses)

        total = analysis_config["total"]
        df = pd.DataFrame(columns=['course_id', ])
