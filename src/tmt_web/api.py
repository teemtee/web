"""API layer for tmt-web."""

import json
import logging
import platform
import time
from datetime import UTC, datetime
from os import environ
from typing import Annotated, Any, Literal

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.params import Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel
from tmt import Logger
from tmt import __version__ as tmt_version
from tmt.utils import GeneralError

from tmt_web import service, settings
from tmt_web.formatters import deserialize_data, format_data
from tmt_web.generators import html_generator

# Record start time for uptime calculation
START_TIME = time.time()

# Create main logger for the API
logger = Logger(logging.getLogger("tmt-web-api"))

app = FastAPI(
    title="tmt Web API",
    description="Web API for checking tmt tests, plans and stories.\n\n"
    "Source code: [github.com/teemtee/web](https://github.com/teemtee/web)\n\n"
    "Report issues at [teemtee/web/issues](https://github.com/teemtee/web/issues)",
    version="1.0.0",
)


class TaskOut(BaseModel):
    """Response model for asynchronous tasks."""

    id: str
    status: str
    result: str | None = None
    status_callback_url: str | None = None


class VersionInfo(BaseModel):
    """Version information model."""

    api: str
    python: str
    tmt: str


class DependencyStatus(BaseModel):
    """Dependency status model."""

    celery: str
    redis: str


class SystemInfo(BaseModel):
    """System information model."""

    platform: str
    hostname: str
    python_implementation: str


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    uptime_seconds: float
    version: VersionInfo
    dependencies: DependencyStatus
    system: SystemInfo


def _validate_parameters(
    test_url: str | None,
    test_name: str | None,
    plan_url: str | None,
    plan_name: str | None,
) -> None:
    """Validate request parameters."""
    if (test_url is None and test_name is not None) or (test_url is not None and test_name is None):
        logger.fail("Both test-url and test-name must be provided together")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both test-url and test-name must be provided together",
        )
    if (plan_url is None and plan_name is not None) or (plan_url is not None and plan_name is None):
        logger.fail("Both plan-url and plan-name must be provided together")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both plan-url and plan-name must be provided together",
        )
    if plan_url is None and plan_name is None and test_url is None and test_name is None:
        logger.fail("At least one of test or plan parameters must be provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of test or plan parameters must be provided",
        )


def _handle_task_result(
    task_result: AsyncResult,  # type: ignore[type-arg]
    out_format: str,
) -> HTMLResponse | JSONResponse | PlainTextResponse:
    """Handle task result and return appropriate response."""
    if task_result.failed():
        error_message = str(task_result.result)
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )

    if task_result.successful() and task_result.result:
        try:
            logger.debug(f"Task result: {task_result.result}")
            # Deserialize the stored data and format it according to the requested format
            result_str = str(task_result.result)  # Ensure we have a string
            data = deserialize_data(result_str)
            logger.debug(f"Deserialized data: {data}")
            formatted_result = format_data(data, out_format, logger)
            logger.debug(f"Formatted result: {formatted_result}")

            if out_format == "html":
                return HTMLResponse(content=formatted_result)
            if out_format == "yaml":
                return PlainTextResponse(content=formatted_result)
            return JSONResponse(content=json.loads(formatted_result))
        except Exception as e:
            logger.fail(f"Error handling task result: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error handling task result: {e}",
            ) from e

    task_out = _to_task_out(task_result, out_format)
    return JSONResponse(content=task_out.model_dump())


def _process_synchronous_request(
    service_args: dict[str, Any],
    out_format: str,
) -> HTMLResponse | JSONResponse | PlainTextResponse:
    """Process request synchronously without Celery."""
    logger.debug("Celery disabled, processing request synchronously")
    result = service.main(**service_args)
    if out_format == "html":
        return HTMLResponse(content=result)
    if out_format == "json":
        return JSONResponse(content=json.loads(result))
    return PlainTextResponse(content=result)


def _process_async_request(
    service_args: dict[str, Any],
    out_format: str,
) -> HTMLResponse | JSONResponse:
    """Process request asynchronously with Celery."""
    logger.debug("Processing request asynchronously with Celery")
    task_result = service.main.delay(**service_args)

    if out_format == "html":
        logger.debug("Generating HTML status callback")
        status_callback_url = f"{settings.API_HOSTNAME}/status/html?task-id={task_result.task_id}"
        return HTMLResponse(
            content=html_generator.generate_status_callback(
                task_result, status_callback_url, logger
            ),
        )

    task_out = _to_task_out(task_result, out_format)
    return JSONResponse(content=task_out.model_dump())


@app.exception_handler(GeneralError)
async def general_exception_handler(request: Request, exc: GeneralError):
    """Global exception handler for all tmt errors."""
    logger.fail(str(exc))

    # Map specific error messages to appropriate status codes
    if "not found" in str(exc).lower():
        status_code = status.HTTP_404_NOT_FOUND
    elif any(
        msg in str(exc).lower()
        for msg in [
            "must be provided together",
            "missing required",
            "invalid combination",
        ]
    ):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


# Sample url: https://tmt.org/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke
# or for plans: https://tmt.org/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic
@app.get("/", response_model=TaskOut | str)
def root(
    request: Request,
    task_id: Annotated[
        str | None,
        Query(
            alias="task-id",
            title="Task ID",
            description="ID of an existing task to retrieve results for",
        ),
    ] = None,
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
            title="Test ref",
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
            title="Plan ref",
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
        ),
    ] = "json",
) -> TaskOut | HTMLResponse | JSONResponse | PlainTextResponse | RedirectResponse:
    """Process a request for test, plan, or both.

    Returns test/plan information in the specified format. For HTML format with Celery enabled,
    returns a status page that will update to show the final result.

    If no parameters are provided, redirects to API documentation.
    """
    # Show API docs if no parameters are provided
    if not request.query_params:
        return RedirectResponse(url="/docs")

    # If task_id is provided, return the task status directly
    if task_id:
        logger.debug(f"Fetching existing task status for {task_id}")
        task_result = service.main.app.AsyncResult(task_id)
        return _handle_task_result(task_result, out_format)

    # Parameter validations for new task creation
    logger.debug("Validating request parameters")
    _validate_parameters(test_url, test_name, plan_url, plan_name)

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

    # Process request based on Celery configuration
    if environ.get("USE_CELERY") == "false":
        return _process_synchronous_request(service_args, out_format)
    return _process_async_request(service_args, out_format)


@app.get("/status")
def get_task_status(
    task_id: Annotated[
        str | None,
        Query(
            alias="task-id",
            title="Task ID",
            description="ID of the task to check status for",
        ),
    ],
) -> TaskOut:
    """Get the status of an asynchronous task."""
    logger.debug(f"Getting task status for {task_id}")
    if not task_id:
        logger.fail("task-id is required")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task-id is required",
        )

    r = service.main.app.AsyncResult(task_id)

    # Check for specific error conditions in the task result
    if r.failed():
        error_message = str(r.result)
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )

    return _to_task_out(r)


@app.get("/status/html", response_class=HTMLResponse)
def get_task_status_html(
    task_id: Annotated[
        str | None,
        Query(
            alias="task-id",
            title="Task ID",
            description="ID of the task to check status for",
        ),
    ],
) -> HTMLResponse:
    """Get the status of an asynchronous task in HTML format."""
    logger.debug(f"Getting HTML task status for {task_id}")
    if not task_id:
        logger.fail("task-id is required")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task-id is required",
        )

    r = service.main.app.AsyncResult(task_id)
    if r.successful() and r.result:
        # For successful tasks, redirect to root endpoint
        return RedirectResponse(
            url=f"{settings.API_HOSTNAME}/?task-id={r.task_id}&format=html",
            status_code=303,  # Use 303 See Other for GET redirects
        )

    status_callback_url = f"{settings.API_HOSTNAME}/status/html?task-id={r.task_id}"
    return HTMLResponse(
        content=html_generator.generate_status_callback(r, status_callback_url, logger),
    )


def _to_task_out(r: AsyncResult, out_format: str = "json") -> TaskOut:  # type: ignore[type-arg]
    """Convert a Celery AsyncResult to a TaskOut response model."""
    # Use the appropriate status callback URL based on the requested format
    status_callback_url = f"{settings.API_HOSTNAME}/status"
    if out_format == "html":
        status_callback_url += "/html"
    status_callback_url += f"?task-id={r.task_id}"

    return TaskOut(
        id=r.task_id,
        status=r.status,
        result=r.traceback if r.failed() else r.result,
        status_callback_url=status_callback_url,
    )


@app.get("/health")
def health_check() -> HealthStatus:
    """Health check endpoint providing detailed system and service status.

    Returns:
        - Service status and uptime
        - Version information for key components
        - System information
        - Dependencies status (Redis, Celery)

    """
    logger.debug("Health check requested")

    # Check Celery/Redis status
    celery_enabled = environ.get("USE_CELERY") != "false"
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
        version=VersionInfo(
            api=app.version,
            python=platform.python_version(),
            tmt=tmt_version,
        ),
        dependencies=DependencyStatus(
            celery=celery_status,
            redis=redis_status,
        ),
        system=SystemInfo(
            platform=platform.platform(),
            hostname=platform.node(),
            python_implementation=platform.python_implementation(),
        ),
    )
