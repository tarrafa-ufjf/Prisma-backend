from __future__ import annotations

import time
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Type

import yaml


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
        super().__init__("engagement")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.engagement_analysis(subject_id, "subject", version, connector)


class StudentPerformanceObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("performance")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.performance_analysis(subject_id, "subject", version, connector)


class StudentMotivationObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("motivation")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.motivation_analysis(subject_id, "subject", version, connector)


class StudentCognitiveObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("cognitive")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.cognitive_analysis(subject_id, "subject", version, connector)


class StudentPedagogicObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("pedagogic")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.pedagogic_analysis(subject_id, "subject", version, connector)


class StudentGiveUpObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("give_up")
        self.analyzer = analyzer

    def calculate(self, subject_id, version, connector, engine, mapper, **context):
        return self.analyzer.give_up_analysis(subject_id, "subject", version, connector)


class TutorResponseForumsObserver(BaseIndicatorObserver):
    def __init__(self, analyzer) -> None:
        super().__init__("response_forums")
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


INDICATOR_OBSERVERS: Dict[str, Type[BaseIndicatorObserver]] = {
    "engagement": StudentEngagementObserver,
    "performance": StudentPerformanceObserver,
    "motivation": StudentMotivationObserver,
    "cognitive": StudentCognitiveObserver,
    "pedagogic": StudentPedagogicObserver,
    "give_up": StudentGiveUpObserver,
    "response_forums": TutorResponseForumsObserver,
    "feedback": TutorFeedbackObserver,
    "login": TutorLoginObserver,
}


def load_indicator_channel_config(config_path: Path) -> Dict[str, Dict[str, List[str]]]:
    with config_path.open("r", encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file) or {}

    if not isinstance(raw_config, dict):
        raise ValueError(f"Invalid indicator config at {config_path}: expected a mapping.")

    config: Dict[str, Dict[str, List[str]]] = {}

    for actor, channels in raw_config.items():
        if not isinstance(actor, str) or not isinstance(channels, dict):
            raise ValueError(
                f"Invalid indicator config at {config_path}: each actor must map to channels."
            )

        config[actor] = {}

        for channel, indicators in channels.items():
            if not isinstance(channel, str) or not isinstance(indicators, list):
                raise ValueError(
                    f"Invalid indicator config at {config_path}: "
                    f"channel '{channel}' must map to a list of indicators."
                )

            for indicator_name in indicators:
                if not isinstance(indicator_name, str):
                    raise ValueError(
                        f"Invalid indicator config at {config_path}: "
                        f"channel '{channel}' has a non-text indicator name."
                    )

            config[actor][channel] = indicators

    return config


def register_default_indicators(
    publisher: IndicatorPublisher,
    analyzer,
    config_path: Path | None = None,
) -> None:
    indicator_config_path = config_path or Path(__file__).with_name("indicator_channels.yml")
    channel_config = load_indicator_channel_config(indicator_config_path)

    for actor, channels in channel_config.items():
        for channel, indicator_names in channels.items():
            for indicator_name in indicator_names:
                observer_class = INDICATOR_OBSERVERS.get(indicator_name)

                if observer_class is None:
                    available = ", ".join(sorted(INDICATOR_OBSERVERS))
                    raise ValueError(
                        f"Unknown indicator '{indicator_name}' in {indicator_config_path}. "
                        f"Available indicators: {available}."
                    )

                publisher.subscribe(actor, channel, observer_class(analyzer))
