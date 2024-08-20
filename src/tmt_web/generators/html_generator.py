from pathlib import Path

from celery.result import AsyncResult
from jinja2 import Environment, FileSystemLoader
from tmt import Logger, Plan, Test

templ_dir = Path(__file__).resolve().parent / 'templates'

env = Environment(loader=FileSystemLoader(str(templ_dir)), autoescape=True)

def render_template(template_name: str, **kwargs) -> str:
    template = env.get_template(template_name)
    return template.render(**kwargs)

def generate_status_callback(r: AsyncResult, status_callback_url: str) -> str:  # type: ignore [type-arg]
    data = {
        "status": r.status,
        "status_callback_url": status_callback_url,
        "result": r.result
    }
    return render_template("status_callback.html.j2", **data)

def generate_html_page(obj: Test | Plan, logger: Logger) -> str:
    logger.print("Generating the HTML file...")
    return render_template('testorplan.html.j2', testorplan=obj)

def generate_testplan_html_page(test: Test, plan: Plan, logger: Logger) -> str:
    logger.print("Generating the HTML file...")
    return render_template('testandplan.html.j2', test=test, plan=plan)

if __name__ == "__main__":
    print("This is not an executable file!")
