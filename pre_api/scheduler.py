import atexit
import os
import signal
import time

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from app import run_scheduled_analysis
from database import DatabaseAdmin

load_dotenv()


def _build_scheduler():
    timezone = os.getenv("SCHEDULER_TIMEZONE", "America/Sao_Paulo")
    scheduler = BackgroundScheduler(timezone=timezone)

    scheduler.add_job(
        run_scheduled_analysis,
        kwargs={"channel": "diario"},
        trigger="cron",
        hour=12,
        minute=48,
        id="daily_analysis",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    scheduler.add_job(
        run_scheduled_analysis,
        kwargs={"channel": "semanal"},
        trigger="cron",
        day_of_week="mon",
        hour=12,
        minute=58,
        id="weekly_analysis",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    scheduler.add_job(
        run_scheduled_analysis,
        kwargs={"channel": "mensal"},
        trigger="cron",
        day=1,
        hour=13,
        minute=8,
        id="monthly_analysis",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
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
