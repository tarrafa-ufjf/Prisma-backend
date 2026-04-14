import pandas as pd
from collections import defaultdict
from database import DatabaseAdmin
from sqlalchemy import MetaData, Table, select

class General_subjects_indicators:
    def __init__(self, mapper):
        self.mapper = mapper
        self.db_admin = DatabaseAdmin()

    def general_subjects_indicators(self, version, connector, institution_id=1):
        df_flags = self._fetch_flags_general(institution_id)
        df_subjects_summary = self.mapper.fetch_subjects_summary(connector, version)

        subjects_info = {
            int(row["subject_id"]): {
                "name": row["name"],
                "abrev": row["abrev"],
                "total_enrolled": int(row["total_enrolled"] or 0),
            }
            for _, row in df_subjects_summary.iterrows()
            if pd.notna(row["subject_id"])
        }

        teachers_by_subject = self._fetch_teachers_map(connector, version, institution_id)

        subjects = []

        for row in df_flags:
            subject_id = int(row["subject_id"])

            info = subjects_info.get(subject_id, {
                "name": None,
                "abrev": None,
                "total_enrolled": 0,
            })

            subjects.append({
                "id": subject_id,
                "name": info["name"],
                "abbrev": info["abrev"],
                "teachers": teachers_by_subject.get(subject_id, []),
                "total_enrolled": info["total_enrolled"],
                "label_engagement": row["label_engagement"],
                "label_motivation": row["label_motivation"],
                "label_performance": row["label_performance"],
                "label_cognitive": row["label_cognitive"],
                "label_relation_teacher_student": row["label_relation_teacher_student"],
                "label_give_up": row["label_give_up"],
                "mean_subject": row["mean_grade_performance"],
            })

        return {"subjects": subjects}

    def _fetch_flags_general(self, institution_id: int = 1):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        global_indicators_students = Table(
            "global_indicators_students",
            metadata,
            autoload_with=engine
        )

        with engine.connect() as conn:
            query = (
                select(
                    global_indicators_students.c.subject_id,
                    global_indicators_students.c.label_engagement,
                    global_indicators_students.c.label_motivation,
                    global_indicators_students.c.label_performance,
                    global_indicators_students.c.label_cognitive,
                    global_indicators_students.c.label_relation_teacher_student,
                    global_indicators_students.c.label_give_up,
                    global_indicators_students.c.mean_grade_performance
                )
                .where(global_indicators_students.c.institution_id == institution_id)
            )

            rows = conn.execute(query).mappings().all()

        return rows

    def _fetch_teachers_map(self, connector, version, institution_id: int):
        engine = self.db_admin.get_connector()
        metadata = MetaData()
        local_indicators_tutors = Table(
            "local_indicators_tutors",
            metadata,
            autoload_with=engine
        )

        with engine.connect() as conn:
            query = (
                select(
                    local_indicators_tutors.c.subject_id,
                    local_indicators_tutors.c.tutor_id
                )
                .where(local_indicators_tutors.c.institution_id == institution_id)
            )

            rows = conn.execute(query).mappings().all()

        if not rows:
            return {}

        tutor_ids = sorted({int(row["tutor_id"]) for row in rows if row["tutor_id"] is not None})

        df_names = self.mapper.fetch_tutors_names_by_ids(connector=connector, version=version, user_ids=tutor_ids)

        name_map = {
            int(row["tutor_id"]): row["full_name"]
            for _, row in df_names.iterrows()
            if pd.notna(row["tutor_id"])
        }

        teachers_by_subject = defaultdict(list)
        seen = set()

        for row in rows:
            if row["subject_id"] is None or row["tutor_id"] is None:
                continue

            subject_id = int(row["subject_id"])
            tutor_id = int(row["tutor_id"])

            key = (subject_id, tutor_id)
            if key in seen:
                continue
            seen.add(key)

            teachers_by_subject[subject_id].append({
                "tutor_id": tutor_id,
                "full_name": name_map.get(tutor_id)
            })

        return dict(teachers_by_subject)