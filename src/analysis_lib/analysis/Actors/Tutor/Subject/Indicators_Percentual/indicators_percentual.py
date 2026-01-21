import unicodedata
from sqlalchemy import MetaData, Table, select, func
from database import DatabaseAdmin
from .....indicator import Indicator


class Indicators_Percentual(Indicator):
    def __init__(self, mapper):
        super().__init__(mapper)
        self.db_admin = DatabaseAdmin()

    def subject_analysis(self, subject_id):
        counts_forums = self._fetch_forums_response_counts(subject_id, institution_id=1)
        perc_good_forums = self._calc_percentage_by_good_labels(
            counts_forums,
            good_labels={"alto", "muito alto"},
        )

        counts_access = self._fetch_access_counts(subject_id, institution_id=1)
        perc_good_access = self._calc_percentage_by_good_labels(
            counts_access,
            good_labels={"alto", "muito alto"},
        )
        
        counts_feedback = self._fetch_feedback_counts(subject_id, institution_id=1)
        perc_good_feedback = self._calc_percentage_by_good_labels(
            counts_feedback,
            good_labels={"alto", "muito alto"},
        )

        return {
            "subject": {
                "id": int(subject_id),
                "good_percentage_response_foruns": perc_good_forums,
                "good_percentage_access": perc_good_access,
                "good_percentage_feedback": perc_good_feedback,
            }
        }

    @staticmethod
    def _normalize_label(raw_label: object):
        """Normaliza: lower, strip, remove acentos. Retorna '' se None."""
        if raw_label is None:
            return ""
        s = str(raw_label).strip().lower()
        if not s:
            return ""
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return s

    def _fetch_label_counts( self, table_name, label_column_name, subject_id, institution_id: int = 1, expected_labels: set[str] | None = None, null_fallback_label = ""):
        """
        Lê a tabela e conta quantos registros há por label.
        - Se não houver nenhuma linha para a turma: retorna _not_processed=True
        - Converte NULL/'' para null_fallback_label (se definido)
        - Normaliza acentos/case (ex: 'Ótimo' -> 'otimo', 'Médio' -> 'medio')
        """
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        t = Table(table_name, metadata, autoload_with=engine)
        label_col = getattr(t.c, label_column_name)

        with engine.connect() as conn:
            query = (
                select(label_col.label("label"), func.count().label("count"))
                .where(t.c.institution_id == institution_id)
                .where(t.c.subject_id == int(subject_id))
                .group_by(label_col)
            )
            rows = conn.execute(query).mappings().all()

        if not rows:
            base = {}
            if expected_labels:
                base.update({k: 0 for k in expected_labels})
            return {**base, "_not_processed": True}

        counts: dict[str, int] = {}
        if expected_labels:
            counts.update({k: 0 for k in expected_labels})

        for row in rows:
            raw = row["label"]
            label = self._normalize_label(raw)

            if not label and null_fallback_label:
                label = null_fallback_label

            if expected_labels and label not in expected_labels:
                continue

            counts[label] = int(row["count"] or 0)

        return counts

    def _fetch_forums_response_counts(self, subject_id, institution_id: int = 1):
        expected = {"muito baixo", "baixo", "medio", "alto", "muito alto"}
        return self._fetch_label_counts(
            table_name="local_indicators_tutors",        
            label_column_name="label_forums_response",   
            subject_id=subject_id,
            institution_id=institution_id,
            expected_labels=expected,
            null_fallback_label="sem_resposta",          
        )

    def _fetch_access_counts(self, subject_id, institution_id: int = 1):
        expected = {"muito baixo", "baixo", "medio", "alto", "muito alto"}
        return self._fetch_label_counts(
            table_name="local_indicators_tutors",
            label_column_name="label_access",      
            subject_id=subject_id,
            institution_id=institution_id,
            expected_labels=expected,
            null_fallback_label="sem_dado", 
        )
        
    def _fetch_feedback_counts(self, subject_id, institution_id: int = 1):
        expected = {"muito baixo", "baixo", "medio", "alto", "muito alto"}
        return self._fetch_label_counts(
            table_name="local_indicators_tutors",
            label_column_name="label_final_feedback",      
            subject_id=subject_id,
            institution_id=institution_id,
            expected_labels=expected,
            null_fallback_label="sem_dado", 
        )

    @staticmethod
    def _calc_percentage_by_good_labels(counts, good_labels):
        """
        Percentual = sum(good_labels) / total * 100
        - Se _not_processed: -1.0
        - Se total == 0: -1.0
        """
        if counts.get("_not_processed", False):
            return -1.0

        total = sum(v for k, v in counts.items() if not str(k).startswith("_"))
        if total == 0:
            return -1.0

        good = sum(counts.get(lbl, 0) for lbl in good_labels)
        return round((good / total) * 100.0, 2)
