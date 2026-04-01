from __future__ import annotations

import time
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List


class BaseIndicatorObserver(ABC):
    """Contract for all indicator observers."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def calculate(
        self,
        subject_id: int,
        version: int,
        connector,
        engine,
        mapper,
        **context,
    ):
        """Run indicator calculation and return a DataFrame-like object."""


class IndicatorPublisher:
    """Publisher that groups subscribers by actor and channel."""

    MYSQL_RETRYABLE = {1205, 1213, 1317, 3024}

    def __init__(self, retries: int = 0, sleep_s: float = 0.3) -> None:
        self.retries = retries
        self.sleep_s = sleep_s
        self.subscribers: DefaultDict[str, DefaultDict[str, List[BaseIndicatorObserver]]] = (
            defaultdict(lambda: defaultdict(list))
        )

    def subscribe(self, actor: str, channel: str, indicator: BaseIndicatorObserver) -> None:
        self.subscribers[actor][channel].append(indicator)

    def notify(
        self,
        actor: str,
        channel: str,
        subject_id: int,
        version: int,
        connector,
        engine,
        mapper,
        **context,
    ) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        for indicator in self.subscribers.get(actor, {}).get(channel, []):
            for attempt in range(self.retries + 1):
                try:
                    df = indicator.calculate(
                        subject_id,
                        version,
                        connector,
                        engine,
                        mapper,
                        **context,
                    )
                    if df is not None and not getattr(df, "empty", False):
                        results[indicator.name] = df
                    break
                except Exception as e:
                    code = None
                    try:
                        if getattr(e, "args", None):
                            code = e.args[0]
                    except Exception:
                        pass

                    print(
                        f"[IndicatorPublisher] actor={actor} channel={channel} indicator={indicator.name} "
                        f"attempt={attempt} code={code} error={e}"
                    )
                    traceback.print_exc()

                    if connector is not None:
                        try:
                            connector.rollback()
                        except Exception:
                            pass
                        try:
                            connector.ping(reconnect=True)
                        except Exception:
                            pass

                    if attempt < self.retries and code in self.MYSQL_RETRYABLE:
                        time.sleep(self.sleep_s)
                        continue

                    errors[indicator.name] = str(e)
                    break

        return {"results": results, "errors": errors}


class StudentEngagementObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("eng")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.engagement_analysis(subject_id, "subject", version, connector)


class StudentPerformanceObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("per")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.performance_analysis(subject_id, "subject", version, connector)


class StudentMotivationObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("mot")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.motivation_analysis(subject_id, "subject", version, connector)


class StudentCognitiveObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("cog")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.cognitive_analysis(subject_id, "subject", version, connector)


class StudentPedagogicObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("ped")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.pedagogic_analysis(subject_id, "subject", version, connector)


class StudentGiveUpObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("giv")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.give_up_analysis(subject_id, "subject", version, connector)


class TutorResponseForumsObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("response_foruns")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.analysis_response_foruns(
            subject_id,
            "subject",
            version,
            connector,
            context.get("start_at"),
            context.get("end_at"),
            tutor_ids=context.get("tutor_ids"),
        )


class TutorFeedbackObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("feedback")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.analysis_feedback(
            subject_id,
            "subject",
            version,
            connector,
            context.get("start_at"),
            context.get("end_at"),
            tutor_ids=context.get("tutor_ids"),
        )


class TutorLoginObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("login")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.analysis_login(
            subject_id,
            "subject",
            version,
            connector,
            context.get("start_at"),
            context.get("end_at"),
            tutor_ids=context.get("tutor_ids"),
        )


def register_default_indicators(publisher: IndicatorPublisher, analyzer) -> None:

    ## Diario
    publisher.subscribe("student", "diario", StudentEngagementObserver(analyzer))
    publisher.subscribe("student", "diario", StudentPerformanceObserver(analyzer))

    publisher.subscribe("tutor", "diario", TutorResponseForumsObserver(analyzer))




    ## Completo
    publisher.subscribe("student", "completo", StudentEngagementObserver(analyzer))
    publisher.subscribe("student", "completo", StudentPerformanceObserver(analyzer))
    publisher.subscribe("student", "completo", StudentMotivationObserver(analyzer))
    publisher.subscribe("student", "completo", StudentCognitiveObserver(analyzer))
    publisher.subscribe("student", "completo", StudentPedagogicObserver(analyzer))
    publisher.subscribe("student", "completo", StudentGiveUpObserver(analyzer))

    publisher.subscribe("tutor", "completo", TutorResponseForumsObserver(analyzer))
    publisher.subscribe("tutor", "completo", TutorFeedbackObserver(analyzer))
    publisher.subscribe("tutor", "completo", TutorLoginObserver(analyzer))
