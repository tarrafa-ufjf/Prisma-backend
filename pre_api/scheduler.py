import atexit
import os
import signal
import time
from datetime import datetime, timezone as datetime_timezone
from pathlib import Path
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import yaml
from app import run_scheduled_analysis
from database import DatabaseAdmin
load_dotenv()
PROTECTED_JOB_KEYS = {"func", "args", "kwargs"}
DEFAULT_JOB_OPTIONS = {
    "trigger": "cron",
    "max_instances": 1,
    "coalesce": True,
    "replace_existing": True,
}
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_HEARTBEAT_INTERVAL_SECONDS", 15))


def _now_utc():
    return datetime.now(datetime_timezone.utc)


def _get_job_channel(job):
    return (job.kwargs or {}).get("channel", job.id)


def _record_scheduler_jobs(scheduler):
    database = DatabaseAdmin()
    heartbeat_at = _now_utc()
    for job in scheduler.get_jobs():
        database.upsert_scheduler_status(
            job_id=job.id,
            channel=_get_job_channel(job),
            process_id=os.getpid(),
            next_run_at=job.next_run_time,
            heartbeat_at=heartbeat_at,
        )


def _record_job_event(scheduler, event):
    job = scheduler.get_job(event.job_id)
    if job is None:
        return

    database = DatabaseAdmin()
    channel = _get_job_channel(job)
    if event.code == EVENT_JOB_SUBMITTED:
        database.upsert_scheduler_status(
            job_id=job.id,
            channel=channel,
            process_id=os.getpid(),
            next_run_at=job.next_run_time,
            heartbeat_at=_now_utc(),
            last_started_at=_now_utc(),
            last_status="running",
            last_error="",
        )
        return

    if event.code == EVENT_JOB_EXECUTED:
        database.upsert_scheduler_status(
            job_id=job.id,
            channel=channel,
            process_id=os.getpid(),
            next_run_at=job.next_run_time,
            heartbeat_at=_now_utc(),
            last_finished_at=_now_utc(),
            last_status="success",
            last_error="",
        )
        return

    if event.code == EVENT_JOB_ERROR:
        database.upsert_scheduler_status(
            job_id=job.id,
            channel=channel,
            process_id=os.getpid(),
            next_run_at=job.next_run_time,
            heartbeat_at=_now_utc(),
            last_finished_at=_now_utc(),
            last_status="failed",
            last_error=str(event.exception)[:1000],
        )


def _load_scheduler_jobs(config_path):
    with config_path.open("r", encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file) or {}
    if not isinstance(raw_config, dict):
        raise ValueError(f"Invalid scheduler config at {config_path}: expected a mapping.")
    raw_jobs = raw_config.get("jobs")
    if not isinstance(raw_jobs, list):
        raise ValueError(f"Invalid scheduler config at {config_path}: 'jobs' must be a list.")
    jobs = []
    for index, raw_job in enumerate(raw_jobs, start=1):
        if not isinstance(raw_job, dict):
            raise ValueError(
                f"Invalid scheduler config at {config_path}: job #{index} must be a mapping."
            )
        job = {**DEFAULT_JOB_OPTIONS, **raw_job}
        job_id = job.get("id")
        channel = job.get("channel")
        if not isinstance(job_id, str) or not job_id:
            raise ValueError(
                f"Invalid scheduler config at {config_path}: job #{index} needs a text id."
            )
        if not isinstance(channel, str) or not channel:
            raise ValueError(
                f"Invalid scheduler config at {config_path}: job '{job_id}' needs a text channel."
            )
        protected_keys = PROTECTED_JOB_KEYS.intersection(job)
        if protected_keys:
            blocked = ", ".join(sorted(protected_keys))
            raise ValueError(
                f"Invalid scheduler config at {config_path}: "
                f"job '{job_id}' cannot define {blocked}."
            )
        jobs.append(job)
    return jobs
def _build_scheduler():
    timezone = os.getenv("SCHEDULER_TIMEZONE", "America/Sao_Paulo")
    config_path = Path(
        os.getenv(
            "SCHEDULER_CONFIG_PATH",
            Path(__file__).with_name("scheduler_jobs.yml"),
        )
    )
    scheduler = BackgroundScheduler(timezone=timezone)
    for job in _load_scheduler_jobs(config_path):
        channel = job.pop("channel")
        scheduler.add_job(
            run_scheduled_analysis,
            kwargs={"channel": channel},
            **job,
        )
    return scheduler
def main():
    scheduler = _build_scheduler()
    scheduler.add_listener(
        lambda event: _record_job_event(scheduler, event),
        EVENT_JOB_SUBMITTED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
    )
    scheduler.start()
    _record_scheduler_jobs(scheduler)
    print(
        "[scheduler] Started. "
        f"timezone={scheduler.timezone}"
    )
    def _shutdown():
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass
        DatabaseAdmin.dispose_connector()
    atexit.register(_shutdown)
    def _signal_handler(signum, frame):
        print(f"[scheduler] Signal {signum} received, shutting down.")
        _shutdown()
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    while True:
        _record_scheduler_jobs(scheduler)
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)
        
if __name__ == "__main__":
    main()
