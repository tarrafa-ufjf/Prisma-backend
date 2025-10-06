import pandas as pd
from typing import List, Dict, Any
from ..indicator import Indicator
from ..Desempenho.performance import Performance 

class Rankings(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
 
    def _ensure_numeric(self, df: pd.DataFrame, cols: List[str]): # Garante que colunas usadas na ordenação/filtragem sejam numéricas
        df = df.copy()
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            else:
                df[c] = 0
        return df

    def _to_ranking_rows(self, df: pd.DataFrame, limit: int):
        rows: List[Dict[str, Any]] = []
        for i, row in df.head(limit).reset_index(drop=True).iterrows():
            name = str(row.get("firstname") or row.get("name") or row.get("fullname") or "")
            user_id = int(row.get("user_id", 0))
            mnn = float(row.get("media_nota_normalizada", 0.0))
            # Se vier normalizada (0..1), multiplica por 100; se já vier 0..100, mantém
            final_grade = round(mnn * 100 if mnn <= 1.0 else mnn, 2)
            percentual = round(float(row.get("media_percentual", 0.0)), 2)
            rows.append({
                "pos": i + 1,
                "user_id": user_id,
                "name": name,
                "final_grade": final_grade,
                "percentual": percentual
            })
        return rows

    def subject_analysis(self, subject_id: int, version, connector, kind: str = "best-performance", limit: int = 10):
        """
        Monta rankings por disciplina (subject).
        kind: 'best-performance' | 'at-risk'
        """
        # 1) Busca dataframe de desempenho por aluno na disciplina
        perf = Performance(self.mapper)
        df = perf.discretized_performance(subject_id, version, connector)

        if df is None or df.empty:
            return {"id": subject_id, "type": kind, "ranking": []}

        # 2) Normaliza colunas que serão usadas
        df = self._ensure_numeric(df, [
            "media_nota_normalizada", "media_percentual",
            "qtd_aprovado", "qtd_reprovado", "qtd_ri",
            "performance_label_global"
        ])

        # 3) Ordena/filtra conforme o tipo
        if kind == "best-performance":
            # Melhor desempenho primeiro:
            #   - maior label de performance
            #   - maior percentual
            #   - maior nota normalizada
            df_sorted = df.sort_values(
                by=["performance_label_global", "media_percentual", "media_nota_normalizada"],
                ascending=[False, False, False]
            )

        elif kind == "at-risk":
            # Em risco:
            #   - baixa performance_label_global
            #   - percentual baixo
            #   - reprovações/RI pesam
            mask = (
                (df["performance_label_global"] <= 1) |
                (df["media_percentual"] < 60) |
                (df["qtd_reprovado"] > 0) |
                (df["qtd_ri"] > 0)
            )
            df_sorted = df[mask].sort_values(
                by=["performance_label_global", "media_percentual", "qtd_reprovado", "qtd_ri"],
                ascending=[True, True, False, False]
            )
        else:
            raise ValueError("invalid 'type'")

        ranking = self._to_ranking_rows(df_sorted, limit)

        return {
            "id": subject_id,
            "type": kind,
            "ranking": ranking
        }