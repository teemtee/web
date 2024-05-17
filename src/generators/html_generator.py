import tmt
from celery.result import AsyncResult
from tmt import Test, Logger, Plan


def generate_status_callback(r: AsyncResult, status_callback_url: str) -> str:
    """
    This function generates the status callback for the HTML file
    :param r: AsyncResult object
    :param status_callback_url: URL for the status callback
    :return:
    """
    if r.status == "PENDING":
        return (f'''<html>
        <head>
        <title>HTML File</title>
        <meta charset="UTF-8">
        </head>
        <body>
        Processing... Try this clicking this url in a few seconds: <a href="{status_callback_url}">{status_callback_url}
        </a> </body>''')
    else:
        return (f'''<html>
        <head>
        <title>HTML File</title>
        <meta charset="UTF-8">
        </head>
        <body>
        Status: {r.status}<br>
        The result is: <br>{r.result}
        </body>''')


def generate_test_html_page(test: Test, logger: Logger) -> str:
    """
    This function generates an HTML file with the input data for a test
    :param test: Test object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the HTML file...")
    full_url = test.web_link()
    # Adding the input data to the HTML file
    file_html = (f'''<html>
    <head>
    <title>HTML File</title>
    <meta charset="UTF-8">
    </head> 
    <body>
    name: {test.name}<br>
    summary: {test.summary}<br>
    description: {test.description}<br>
    url: <a href=\"{full_url}\" target=\"_blank\">{full_url}</a><br>
    ref: {test.fmf_id.ref}<br>
    contact: {test.contact}<br>
    tag: {test.tag}<br>
    tier: {test.tier}<br>
    id: {test.id}<br>
    fmf-id:<br>
    <ul>
      <li>url: {test.fmf_id.url}</li>
      <li>path: {test.fmf_id.path.as_posix() if test.fmf_id.path is not None else None}</li>
      <li>name: {test.fmf_id.name}</li>
      <li>ref: {test.fmf_id.ref}</li>
    </ul>
    </body>
    </html>''')
    logger.print("HTML file generated successfully!", color="green")
    return file_html


def generate_plan_html_page(plan: Plan, logger: Logger) -> str:
    """
    This function generates an HTML file with the input data for a plan
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the HTML file...")
    full_url = plan.web_link()
    # Adding the input data to the HTML file
    file_html = (f'''<html>
    <head>
    <title>HTML File</title>
    <meta charset="UTF-8">
    </head> 
    <body>
    name: {plan.name}<br>
    summary: {plan.summary}<br>
    description: {plan.description}<br>
    url: <a href=\"{full_url}\" target=\"_blank\">{full_url}</a><br>
    ref: {plan.fmf_id.ref}<br>
    contact: {plan.contact}<br>
    tag: {plan.tag}<br>
    tier: {plan.tier}<br>
    id: {plan.id}<br>
    fmf-id:<br>
    <ul>
      <li>url: {plan.fmf_id.url}</li>
      <li>path: {plan.fmf_id.path.as_posix() if plan.fmf_id.path is not None else None}</li>
      <li>name: {plan.fmf_id.name}</li>
      <li>ref: {plan.fmf_id.ref}</li>
    </ul>
    </body>
    </html>''')
    logger.print("HTML file generated successfully!", color="green")
    return file_html


def generate_testplan_html_page(test: tmt.Test, plan: tmt.Plan, logger: Logger) -> str:
    """
    This function generates an HTML file with the input data for a test and a plan
    :param test: Test object
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the HTML file...")
    full_url_test = test.web_link()
    full_url_plan = plan.web_link()
    # Adding the input data to the HTML file
    file_html = (f'''<html>
    <head>
    <title>HTML File</title>
    <meta charset="UTF-8">
    </head> 
    <body>
    Test metadata<br>
    name: {test.name}<br>
    summary: {test.summary}<br>
    description: {test.description}<br>
    url: <a href=\"{full_url_test}\" target=\"_blank\">{full_url_test}</a><br>
    ref: {test.fmf_id.ref}<br>
    contact: {test.contact}<br>
    tag: {test.tag}<br>
    tier: {test.tier}<br>
    id: {test.id}<br>
    fmf-id:<br>
    <ul>
      <li>url: {test.fmf_id.url}</li>
      <li>path: {test.fmf_id.path.as_posix() if test.fmf_id.path is not None else None}</li>
      <li>name: {test.fmf_id.name}</li>
      <li>ref: {test.fmf_id.ref}</li>
    </ul>
    <br>
    Plan metadata<br>
    name: {plan.name}<br>
    summary: {plan.summary}<br>
    description: {plan.description}<br>
    url: <a href=\"{full_url_plan}\" target=\"_blank\">{full_url_plan}</a><br>
    ref: {plan.fmf_id.ref}<br>
    contact: {plan.contact}<br>
    tag: {plan.tag}<br>
    tier: {plan.tier}<br>
    id: {plan.id}<br>
    fmf-id:<br>
    <ul>
      <li>url: {plan.fmf_id.url}</li>
      <li>path: {plan.fmf_id.path.as_posix() if plan.fmf_id.path is not None else None}</li>
      <li>name: {plan.fmf_id.name}</li>
      <li>ref: {plan.fmf_id.ref}</li>
    </ul>
    </body>
    </html>''')
    logger.print("HTML file generated successfully!", color="green")
    return file_html


if __name__ == "__main__":
    print("This is not executable file!")
