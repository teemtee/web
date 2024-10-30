from pathlib import Path

from celery.result import AsyncResult
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from tmt import Logger, Plan, Test
from tmt.utils import GeneralError

# Template directory is in the tmt_web package
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"

# Initialize Jinja environment with template directory
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


def _render_template(template_name: str, logger: Logger, **kwargs) -> str:
    """
    Helper function to render a template with error handling.

    :param template_name: Name of the template to render
    :param logger: Logger instance for logging
    :param kwargs: Template variables
    :return: Rendered template as string
    :raises: GeneralError if template rendering fails
    """
    try:
        logger.debug(f"Loading template '{template_name}'")
        template = env.get_template(template_name)
        logger.debug("Rendering template")
        return template.render(**kwargs)
    except TemplateNotFound as err:
        logger.fail(f"Template '{template_name}' not found")
        raise GeneralError(f"Template '{template_name}' not found in {TEMPLATE_DIR}") from err
    except Exception as err:
        logger.fail("Failed to render template")
        raise GeneralError(f"Failed to render template '{template_name}'") from err


def generate_status_callback(result: AsyncResult, status_callback_url: str, logger: Logger) -> str:  # type: ignore [type-arg]
    """
    Generate HTML status callback page.

    :param result: Celery task result
    :param status_callback_url: URL for status callback
    :param logger: Logger instance for logging
    :return: Rendered HTML page
    :raises: GeneralError if template rendering fails
    """
    logger.debug("Generating status callback page")
    data = {
        "status": result.status,
        "status_callback_url": status_callback_url,
        "result": result.result
    }
    return _render_template("status_callback.html.j2", logger=logger, **data)


def generate_html_page(obj: Test | Plan, logger: Logger) -> str:
    """
    Generate HTML page for a test or plan.

    :param obj: Test or Plan object to render
    :param logger: Logger instance for logging
    :return: Rendered HTML page
    :raises: GeneralError if template rendering fails
    """
    logger.debug("Generating HTML page")
    result = _render_template("testorplan.html.j2", logger=logger, testorplan=obj)
    logger.debug("HTML page generated")
    return result


def generate_testplan_html_page(test: Test, plan: Plan, logger: Logger) -> str:
    """
    Generate HTML page for both test and plan.

    :param test: Test object to render
    :param plan: Plan object to render
    :param logger: Logger instance for logging
    :return: Rendered HTML page
    :raises: GeneralError if template rendering fails
    """
    logger.debug("Generating HTML page")
    result = _render_template("testandplan.html.j2", logger=logger, test=test, plan=plan)
    logger.debug("HTML page generated")
    return result
