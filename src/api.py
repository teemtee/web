from flask import Flask, request
from src import service

app = Flask(__name__)


# Sample url: https://tmt.org/?url=https://github.com/teemtee/tmt&name=/tests/core/smoke
# or for plans: https://tmt.org/?url=https://github.com/teemtee/tmt&name=/plans/features/basic&type=plan
@app.route("/", methods=["GET"])
def find_test():
    test_url = request.args.get("test_url", default=None)
    test_name = request.args.get("test_name", default=None)
    test_ref = request.args.get("test_ref", default="main")
    if (test_url is None and test_name is not None) or (test_url is not None and test_name is None):
        return "Invalid arguments!"
    plan_url = request.args.get("plan_url", default=None)
    plan_name = request.args.get("plan_name", default=None)
    plan_ref = request.args.get("plan_ref", default="main")
    if (plan_url is None and plan_name is not None) or (plan_url is not None and plan_name is None):
        return "Invalid arguments!"
    html_page = service.main(test_url, test_name, test_ref, plan_url, plan_name, plan_ref)
    return html_page


if __name__ == "__main__":
    app.run(debug=False)
