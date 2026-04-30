import atexit
import os
import signal
import time
from pathlib import Path
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
    scheduler.start()
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
        time.sleep(1)
        
if __name__ == "__main__":
    main()
