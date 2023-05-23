import uuid
import pathlib

from datetime import datetime
from typing import Callable

from celery import shared_task, group
from celery.result import AsyncResult, GroupResult
from celery.utils.log import get_task_logger

from mastf.core.files import TaskFileHandler
from mastf.core.progress import Observer

from mastf.MASTF import settings
from mastf.MASTF.models import Scan, ScanTask, Scanner, File, Details
from mastf.MASTF.scanners.plugin import ScannerPlugin
from mastf.MASTF.scanners.sast import SastIntegration

logger = get_task_logger(__name__)

__all__ = ["perform_async_sast"]

@shared_task(bind=True)
def perform_async_sast(self, scan_task_id: str, file_dir) -> None:
    scan_task = ScanTask.objects.get(task_uuid=scan_task_id)
    scan_task.celery_id = self.request.id
    scan_task.save()
    observer = Observer(self, scan_task=scan_task)

    try:
        sast = SastIntegration(
            observer=observer,
            rules_dir=(settings.BASE_DIR / "android" / "rules"),
            excluded=["re:.*/android/.*", "re:.*/smali/.*"],
            scan_task=scan_task
        )
        observer.update("Running pySAST scan...", do_log=True)
        sast.start(pathlib.Path(file_dir) / "src")
        _, meta = observer.success("Finished pySAST scan!")
        return meta
    except Exception as err:
        _, meta = observer.exception(err, "Failed to execute pySAST successfully!")
        return meta