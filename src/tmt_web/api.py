"""API layer for tmt-web using FastAPI background tasks and Valkey."""

import json
import logging
import platform
import time
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.params import Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel
from tmt import Logger
from tmt import __version__ as tmt_version
from tmt.utils import GeneralError

from tmt_web import service, settings
from tmt_web.formatters import deserialize_data, format_data
from tmt_web.generators import html_generator
from tmt_web.utils.task_manager import FAILURE, SUCCESS, task_manager

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

    valkey: str


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
    task_id: str,
    out_format: str,
) -> HTMLResponse | JSONResponse | PlainTextResponse:
    """Handle task result and return appropriate response."""
    task_info = task_manager.get_task_info(task_id)

    if task_info["status"] == FAILURE:
        error_message = task_info.get("error", "Unknown error")
        if error_message and "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message or "Task failed",
        )

    if task_info["status"] == SUCCESS and task_info["result"]:
        try:
            logger.debug(f"Task result: {task_info['result']}")
            result_str = str(task_info["result"])

            # Check if result is already formatted or needs formatting
            try:
                # Try to deserialize - if it works, the result needs formatting
                data = deserialize_data(result_str)
                formatted_result = format_data(data, out_format, logger)
            except Exception:
                # If deserialization fails, assume the result is already formatted
                formatted_result = result_str

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

    task_out = _to_task_out(task_info, out_format)
    return JSONResponse(content=task_out.model_dump())


# Sample url: https://tmt.org/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke
# or for plans: https://tmt.org/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic
@app.get("/", response_model=TaskOut | str)
def root(
    request: Request,
    background_tasks: BackgroundTasks,
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
    ] = "html",
) -> TaskOut | HTMLResponse | JSONResponse | PlainTextResponse | RedirectResponse:
    """Process a request for test, plan, or both.

    Returns test/plan information in the specified format. For HTML format,
    returns a status page that will update to show the final result.

    If no parameters are provided, redirects to API documentation.
    """
    # Show API docs if no parameters are provided
    if not request.query_params:
        return RedirectResponse(url="/docs")

    # If task_id is provided, return the task status directly
    if task_id:
        logger.debug(f"Fetching existing task status for {task_id}")
        return _handle_task_result(task_id, out_format)

    # Parameter validations for new task creation
    logger.debug("Validating request parameters")
    _validate_parameters(test_url, test_name, plan_url, plan_name)

    # Process request with background tasks
    task_id = service.process_request(
        background_tasks=background_tasks,
        test_url=test_url,
        test_name=test_name,
        test_ref=test_ref,
        test_path=test_path,
        plan_url=plan_url,
        plan_name=plan_name,
        plan_ref=plan_ref,
        plan_path=plan_path,
        out_format=out_format,
    )

    # If HTML format, generate a callback page
    if out_format == "html":
        logger.debug("Generating HTML status callback")
        status_callback_url = f"{settings.API_HOSTNAME}/status/html?task-id={task_id}"
        return HTMLResponse(
            content=html_generator.generate_status_callback(task_id, status_callback_url, logger),
        )

    # For other formats, return a JSON response with task information
    task_info = task_manager.get_task_info(task_id)
    task_out = _to_task_out(task_info, out_format)
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

    task_info = task_manager.get_task_info(task_id)

    # Check for specific error conditions in the task result
    if task_info["status"] == FAILURE:
        error_message = task_info.get("error", "Unknown error")
        if error_message and "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )

    return _to_task_out(task_info)


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

    task_info = task_manager.get_task_info(task_id)

    if task_info["status"] == SUCCESS and task_info["result"]:
        # For successful tasks, redirect to root endpoint
        return RedirectResponse(
            url=f"{settings.API_HOSTNAME}/?task-id={task_id}",
            status_code=303,  # Use 303 See Other for GET redirects
        )

    status_callback_url = f"{settings.API_HOSTNAME}/status/html?task-id={task_id}"

    # For FAILURE status, use the error message if available
    result = task_info.get("result")
    if task_info["status"] == FAILURE and task_info.get("error"):
        result = task_info["error"]

    return HTMLResponse(
        content=html_generator.generate_status_callback(
            task_id,
            status_callback_url,
            logger,
            status=task_info["status"],
            result=result,
        ),
    )


def _to_task_out(task_info: dict[str, Any], out_format: str = "json") -> TaskOut:
    """Convert a task info dict to a TaskOut response model."""
    # Use the appropriate status callback URL based on the requested format
    status_callback_url = f"{settings.API_HOSTNAME}/status"
    if out_format == "html":
        status_callback_url += "/html"
    status_callback_url += f"?task-id={task_info['id']}"

    return TaskOut(
        id=task_info["id"],
        status=task_info["status"],
        result=task_info.get("error")
        if task_info["status"] == FAILURE
        else task_info.get("result"),
        status_callback_url=status_callback_url,
    )


@app.get("/health")
def health_check() -> HealthStatus:
    """Health check endpoint providing detailed system and service status.

    Returns:
        - Service status and uptime
        - Version information for key components
        - System information
        - Dependencies status (Valkey)
    """
    logger.debug("Health check requested")

    # Check Valkey status
    valkey_status = "ok"
    try:
        # Ping Valkey
        task_manager.client.ping()
    except Exception:
        valkey_status = "failed"

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
            valkey=valkey_status,
        ),
        system=SystemInfo(
            platform=platform.platform(),
            hostname=platform.node(),
            python_implementation=platform.python_implementation(),
        ),
    )
