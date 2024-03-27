from flask import Flask, request
from src import service

app = Flask(__name__)


# Sample url: https://tmt.org/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke
# or for plans: https://tmt.org/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic
@app.route("/", methods=["GET"])
def find_test():
    test_url = request.args.get("test-url", default=None)
    test_name = request.args.get("test-name", default=None)
    test_ref = request.args.get("test-ref", default="main")
    if (test_url is None and test_name is not None) or (test_url is not None and test_name is None):
        return "Invalid arguments!"
    plan_url = request.args.get("plan-url", default=None)
    plan_name = request.args.get("plan-name", default=None)
    plan_ref = request.args.get("plan-ref", default="main")
    if (plan_url is None and plan_name is not None) or (plan_url is not None and plan_name is None):
        return "Invalid arguments!"
    html_page = service.main(test_url, test_name, test_ref, plan_url, plan_name, plan_ref)
    return html_page


if __name__ == "__main__":
    app.run(debug=False)
