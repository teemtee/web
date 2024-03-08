import tmt
from tmt import Test, Logger, Plan


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
    file_html = ('''<html>
    <head>
    <title>HTML File</title>
    <meta charset="UTF-8">
    </head> 
    <body>
    name: ''' + str(test.name) + '''<br>
    summary: ''' + str(test.summary) + '''<br>
    url: <a href=\"''' + full_url + "\" target=\"_blank\">" + full_url + '''</a><br>
    ref: ''' + str(test.fmf_id.ref) + '''<br>
    contact: ''' + str(test.contact) + '''<br>
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
    file_html = ('''<html>
    <head>
    <title>HTML File</title>
    <meta charset="UTF-8">
    </head> 
    <body>
    name: ''' + str(plan.name) + '''<br>
    summary: ''' + str(plan.summary) + '''<br>
    url: <a href=\"''' + full_url + "\" target=\"_blank\">" + full_url + '''</a><br>
    ref: ''' + str(plan.fmf_id.ref) + '''<br>
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
    file_html = ('''<html>
    <head>
    <title>HTML File</title>
    <meta charset="UTF-8">
    </head> 
    <body>
    name: ''' + str(test.name) + '''<br>
    summary: ''' + str(test.summary) + '''<br>
    url: <a href=\"''' + full_url_test + "\" target=\"_blank\">" + full_url_test + '''</a><br>
    ref: ''' + str(test.fmf_id.ref) + '''<br>
    contact: ''' + str(test.contact) + '''<br>
    <br>
    name: ''' + str(plan.name) + '''<br>
    summary: ''' + str(plan.summary) + '''<br>
    url: <a href=\"''' + full_url_plan + "\" target=\"_blank\">" + full_url_plan + '''</a><br>
    ref: ''' + str(plan.fmf_id.ref) + '''<br>
    </body>
    </html>''')
    logger.print("HTML file generated successfully!", color="green")
    return file_html


if __name__ == "__main__":
    print("This is not executable file!")
