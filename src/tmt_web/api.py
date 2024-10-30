import logging
import os
import platform
import time
from datetime import UTC, datetime
from typing import Annotated, Literal

from celery.result import AsyncResult
from fastapi import FastAPI, Request, status
from fastapi.params import Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel
from tmt import Logger
from tmt import __version__ as tmt_version
from tmt.utils import GeneralError

from tmt_web import service, settings
from tmt_web.generators import html_generator

# Record start time for uptime calculation
START_TIME = time.time()

# Create main logger for the API
logger = Logger(logging.getLogger("tmt-web-api"))

app = FastAPI(
    title="tmt Web API",
    description="Web API for checking tmt tests, plans and stories",
    version="1.0.0",
)


class TaskOut(BaseModel):
    """Response model for asynchronous tasks."""
    id: str
    status: str
    result: str | None = None
    status_callback_url: str | None = None


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    uptime_seconds: float
    version: dict[str, str]
    dependencies: dict[str, str]
    system: dict[str, str]


@app.exception_handler(GeneralError)
async def general_exception_handler(request: Request, exc: GeneralError):
    """Global exception handler for all tmt errors"""
    logger.fail(str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# Sample url: https://tmt.org/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke
# or for plans: https://tmt.org/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic
@app.get("/", response_model=TaskOut | str)
def root(
        request: Request,
        test_url: Annotated[
            str | None,
            Query(
                alias="test-url",
                title="Test URL",
                description="URL of a Git repository containing test metadata",
            ),
        ] = None,
        test_name: Annotated[
            str | None,
            Query(
                alias="test-name",
                title="Test name",
                description="Name of the test",
            ),
        ] = None,
        test_ref: Annotated[
            str | None,
            Query(
                alias="test-ref",
                title="Test reference",
                description="Reference of the test repository",
            ),
        ] = None,
        test_path: Annotated[
            str | None,
            Query(
                alias="test-path",
                title="Test path",
                description="Path to the test metadata directory",
            ),
        ] = None,
        plan_url: Annotated[
            str | None,
            Query(
                alias="plan-url",
                title="Plan URL",
                description="URL of a Git repository containing plan metadata",
            ),
        ] = None,
        plan_name: Annotated[
            str | None,
            Query(
                alias="plan-name",
                title="Plan name",
                description="Name of the plan",
            ),
        ] = None,
        plan_ref: Annotated[
            str | None,
            Query(
                alias="plan-ref",
                title="Plan reference",
                description="Reference of the plan repository",
            ),
        ] = None,
        plan_path: Annotated[
            str | None,
            Query(
                alias="plan-path",
                title="Plan path",
                description="Path to the plan metadata directory",
            ),
        ] = None,
        out_format: Annotated[
            Literal["html", "json", "yaml"],
            Query(
                alias="format",
                description="Output format for the response",
            )
        ] = "json",
) -> TaskOut | HTMLResponse | JSONResponse | PlainTextResponse | RedirectResponse:
    """
    Process a request for test, plan, or both.

    Returns test/plan information in the specified format. For HTML format with Celery enabled,
    returns a status page that will update to show the final result.

    If no parameters are provided, redirects to API documentation.
    """
    # Show API docs if no parameters are provided
    if not request.query_params:
        return RedirectResponse(url="/docs")

    # Parameter validations
    logger.debug("Validating request parameters")
    if (test_url is None and test_name is not None) or (test_url is not None and test_name is None):
        logger.fail("Both test-url and test-name must be provided together")
        raise GeneralError("Both test-url and test-name must be provided together")
    if (plan_url is None and plan_name is not None) or (plan_url is not None and plan_name is None):
        logger.fail("Both plan-url and plan-name must be provided together")
        raise GeneralError("Both plan-url and plan-name must be provided together")
    if plan_url is None and plan_name is None and test_url is None and test_name is None:
        logger.fail("At least one of test or plan parameters must be provided")
        raise GeneralError("At least one of test or plan parameters must be provided")

    service_args = {
        "test_url": test_url,
        "test_name": test_name,
        "test_ref": test_ref,
        "plan_url": plan_url,
        "plan_name": plan_name,
        "plan_ref": plan_ref,
        "out_format": out_format,
        "test_path": test_path,
        "plan_path": plan_path,
    }

    # Disable Celery if not needed
    if os.environ.get("USE_CELERY") == "false":
        logger.debug("Celery disabled, processing request synchronously")
        response_by_output = {
            "html": HTMLResponse,
            "json": JSONResponse,
            "yaml": PlainTextResponse,
        }

        response = response_by_output.get(out_format, PlainTextResponse)
        return response(service.main(**service_args))

    logger.debug("Processing request asynchronously with Celery")
    r = service.main.delay(**service_args)

    # Handle response based on format
    if out_format == "html":
        logger.debug("Generating HTML status callback")
        status_callback_url = f"{settings.API_HOSTNAME}/status/html?task-id={r.task_id}"
        return HTMLResponse(
            content=html_generator.generate_status_callback(r, status_callback_url, logger)
        )
    elif out_format == "yaml":
        task_out = _to_task_out(r)
        return PlainTextResponse(content=task_out.model_dump_json())
    else:
        return _to_task_out(r)


@app.get("/status", response_model=TaskOut)
def get_task_status(task_id: Annotated[str | None,
            Query(
                alias="task-id",
                title="Task ID",
                description="ID of the task to check status for",
            )
        ]) -> TaskOut:
    """Get the status of an asynchronous task."""
    logger.debug(f"Getting task status for {task_id}")
    if task_id is None:
        logger.fail("task-id is required")
        raise GeneralError("task-id is required")

    r = service.main.app.AsyncResult(task_id)
    return _to_task_out(r)


@app.get("/status/html", response_class=HTMLResponse)
def get_task_status_html(task_id: Annotated[str | None,
            Query(
                alias="task-id",
                title="Task ID",
                description="ID of the task to check status for",
            )
        ]) -> HTMLResponse:
    """Get the status of an asynchronous task in HTML format."""
    logger.debug(f"Getting HTML task status for {task_id}")
    if task_id is None:
        logger.fail("task-id is required")
        raise GeneralError("task-id is required")

    r = service.main.app.AsyncResult(task_id)
    if r.successful() and r.result:
        return HTMLResponse(content=r.result)
    status_callback_url = (
        f"{settings.API_HOSTNAME}/status/html?task-id={r.task_id}"
    )
    return HTMLResponse(
        content=html_generator.generate_status_callback(r, status_callback_url, logger)
    )


def _to_task_out(r: AsyncResult) -> TaskOut:  # type: ignore [type-arg]
    """Convert a Celery AsyncResult to a TaskOut response model."""
    return TaskOut(
        id=r.task_id,
        status=r.status,
        result=r.traceback if r.failed() else r.result,
        status_callback_url=f"{settings.API_HOSTNAME}/status?task-id={r.task_id}",
    )


@app.get("/health", response_model=HealthStatus)
def health_check() -> HealthStatus:
    """
    Health check endpoint providing detailed system and service status.

    Returns:
        - Service status and uptime
        - Version information for key components
        - System information
        - Dependencies status (Redis, Celery)
    """
    logger.debug("Health check requested")

    # Check Celery/Redis status
    celery_enabled = os.environ.get("USE_CELERY") != "false"
    celery_status = "ok"
    redis_status = "ok"

    if not celery_enabled:
        celery_status = "disabled"
        redis_status = "disabled"
    else:
        try:
            # Ping Redis through Celery
            service.main.app.control.ping(timeout=1.0)
        except Exception:
            celery_status = "failed"
            redis_status = "failed"

    return HealthStatus(
        status="ok",
        timestamp=datetime.now(UTC),
        uptime_seconds=time.time() - START_TIME,
        version={
            "api": app.version,
            "python": platform.python_version(),
            "tmt": tmt_version,
        },
        dependencies={
            "celery": celery_status,
            "redis": redis_status,
        },
        system={
            "platform": platform.platform(),
            "hostname": platform.node(),
            "python_implementation": platform.python_implementation(),
        },
    )
