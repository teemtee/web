# web
Web app for checking tmt tests and plans
# Run instructions
1. Create a virtual environment
2. Install the requirements
3. Use the `start_api.sh` script to start the api
## Tests
To run the tests, use the pytest command
# API
API for checking tmt tests and plans metadata
## Version
The API version is defined by prefix in url, e.g.
`/v0.1/status`
## Endpoints
* `/` - returns ID of the created Celery task with additional metadata in JSON and callback url for `/status` endpoint, 
returns the same in HTML format if `format` is set to `html`
  * `test-url` - URL of the repo test is located in - accepts a `string`

  * `test-ref` - Ref of the repository the test is located in - accepts a `string`, 
  defaults to default branch of the repo
  * `test-path` - Points to directory where `fmf` tree is stored
  * `test-name` - Name of the test - accepts a `string`
  * `plan-url` - URL of the repo plan is located in - accepts a `string`
  
  * `plan-ref` - Ref of the repository the plan is located in - accepts a `string`, 
  defaults to default branch of the repo
  * `plan-path` - Points to directory where `fmf` tree is stored
  * `plan-name` - Name of the plan - accepts a `string`
  * `format` - Format of the output - accepts a `string`, default is `json`, other options are `xml`, `html`
  (serves as a basic human-readable output format)
  * `id` - Unique ID of the tmt object
* `/status` - returns a status of the tmt object being processed by the backend
  * `task_id` - ID of the task - accepts a `string`
* `/status/html` - returns a status of the tmt object being processed by the backend in a simple HTML formatting
  * `task_id` - ID of the task - accepts a `string`
* `/health` - returns a health status of the service

If we want to display metadata for both tests and plans, we can combine the `test-*`
and `plan-*` options together, they are not mutually exclusive.

`test-url` and `test-name`, or `plan-url` and `plan-name` are required.
