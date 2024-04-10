# web
Web app for checking tmt tests, plans and stories
# Run instructions
1. Create a virtual environment
2. Install the requirements
3. Use the `start_api.sh` script to start the api
## Tests
To run the tests, use the pytest command

# Requirements
## As a user I want to have a clickable link to test/plan verifying the issue
Covered by this [issue](https://issues.redhat.com/browse/TT-207). Implemented by creating an API, that will upon request clone the git repository, 
parse the test/plan and return metadata in mainly machine-readable format (but a basic `html` output should
be included as well). Test/plan is identified by fmf id given to the API as a
url parameters. The method for attaching the link to the JIRA issue is up for discussion, but it
should be a part of `tmt` codebase itself and would include a simple call to JIRA API.
There is an option to include a simple web app, that would take the machine-readable output from
the service and present it in a browser in human-readable form.
The service should have a option for authentication, so it would support accessing internal RedHat repositories.


## As AutoMiloš I want to execute relevant tests when the issue is switched to given state
Covered by this [issue](https://issues.redhat.com/browse/TT-261). There is a option to use the
the url given to the service (f.e. `https://tmt.org/?url=https://github.com/teemtee/tmt&name=/tests/smoke&plan-name=/plans/features/core`)
for identifying the test/plan that should be run and then to include additional fields needed for scheduling
the run by AutoMiloš on Testing Farm.