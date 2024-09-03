import os
from typing import Annotated, Any, Literal

from celery.result import AsyncResult
from fastapi import FastAPI
from fastapi.params import Query
from pydantic import BaseModel
from starlette.responses import HTMLResponse

from tmt_web import service
from tmt_web.generators import html_generator

app = FastAPI()


class TaskOut(BaseModel):
    id: str
    status: str
    result: str | None = None
    status_callback_url: str | None = None


# Sample url: https://tmt.org/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke
# or for plans: https://tmt.org/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic
@app.get("/")
def find_test(
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
        out_format: Annotated[Literal["html", "json", "yaml"], Query(alias="format")] = "json",
) -> TaskOut | str | Any:
    # Parameter validations
    if (test_url is None and test_name is not None) or (test_url is not None and test_name is None):
        return "Invalid arguments!"
    if (plan_url is None and plan_name is not None) or (plan_url is not None and plan_name is None):
        return "Invalid arguments!"
    if plan_url is None and plan_name is None and test_url is None and test_name is None:
        return "Missing arguments!"
        # TODO: forward to docs
    # Disable Celery if not needed
    if os.environ.get("USE_CELERY") == "false":
        return service.main(
            test_url=test_url,
            test_name=test_name,
            test_ref=test_ref,
            plan_url=plan_url,
            plan_name=plan_name,
            plan_ref=plan_ref,
            out_format=out_format,
            test_path=test_path,
            plan_path=plan_path)
    r = service.main.delay(
            test_url=test_url,
            test_name=test_name,
            test_ref=test_ref,
            plan_url=plan_url,
            plan_name=plan_name,
            plan_ref=plan_ref,
            out_format=out_format,
            test_path=test_path,
            plan_path=plan_path)
    # Special handling of response if the format is html
    if out_format == "html":
        status_callback_url = f'{os.getenv("API_HOSTNAME")}/status/html?task-id={r.task_id}'
        return HTMLResponse(content=html_generator.generate_status_callback(r, status_callback_url))
    else:
        return _to_task_out(r)


@app.get("/status")
def status(task_id: Annotated[str | None,
            Query(
                alias="task-id",
                title="Task ID",
            )
        ]) -> TaskOut | str:
    r = service.main.app.AsyncResult(task_id)
    return _to_task_out(r)

@app.get("/status/html")
def status_html(task_id: Annotated[str | None,
            Query(
                alias="task-id",
                title="Task ID",
            )
        ]) -> HTMLResponse:
    r = service.main.app.AsyncResult(task_id)
    status_callback_url = f'{os.getenv("API_HOSTNAME")}/status/html?task-id={r.task_id}'
    return HTMLResponse(content=html_generator.generate_status_callback(r, status_callback_url))


def _to_task_out(r: AsyncResult) -> TaskOut:  # type: ignore [type-arg]
    return TaskOut(
        id=r.task_id,
        status=r.status,
        result=r.traceback if r.failed() else r.result,
        status_callback_url=f'{os.getenv("API_HOSTNAME")}/status?task-id={r.task_id}'
    )

@app.get("/health")
def health_check():
    return {"status": "healthy"}
