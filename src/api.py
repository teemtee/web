from fastapi.params import Query
from flask import Flask, request
from src import service
from fastapi import FastAPI

app = FastAPI()


# Sample url: https://tmt.org/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke
# or for plans: https://tmt.org/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic
@app.get("/")
def find_test(
    test_url: str = Query(None, alias="test-url"),
    test_name: str = Query(None, alias="test-name"),
    test_ref: str = Query("main", alias="test-ref"),
    plan_url: str = Query(None, alias="plan-url"),
    plan_name: str = Query(None, alias="plan-name"),
    plan_ref: str = Query("main", alias="plan-ref"),
    out_format: str = Query("json", alias="format")
):
    if (test_url is None and test_name is not None) or (test_url is not None and test_name is None):
        return "Invalid arguments!"
    if (plan_url is None and plan_name is not None) or (plan_url is not None and plan_name is None):
        return "Invalid arguments!"
    html_page = service.main(test_url, test_name, test_ref, plan_url, plan_name, plan_ref)
    return html_page
