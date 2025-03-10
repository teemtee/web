# tmt web

Web application for checking tmt tests, plans and stories.

## Run instructions

To run the service locally for development purposes, use the following command:

```bash
podman-compose up --build
```

Add `-d` for the service to run in the background.

For quick development without container setup:

```bash
CLONE_DIR_PATH=/var/tmp/test uvicorn tmt_web.api:app --reload --host 0.0.0.0 --port 8000
```

## Tests

To run the tests, use the `pytest` command (assuming the service is running).

Alternatively, if you have `hatch` installed, `hatch run dev:test` command will
rebuild, start the service and run the tests.

Run `hatch env show` to see the list of available environments and their scripts.

## Environment variables

- `VALKEY_URL` - *optional*, connection URL for Valkey which is used for storing task state,
  default value is: `valkey://localhost:6379`
- `CLONE_DIR_PATH` - *optional*, specifies the path where the repositories will
  be cloned, default value is: `./.repos/`
- `API_HOSTNAME` - *required*, specifies the hostname of the API, used for
  creating the callback URL to the service

## Architecture

The application uses FastAPI's built-in background tasks for asynchronous processing and
Valkey for task state storage. This architecture provides a lightweight and efficient
solution for handling long-running tasks without requiring external task queue infrastructure.

## API

The API version is defined by prefix in url, e.g. `/v0.1/status`.

If we want to display metadata for both tests and plans, we can combine
the `test-*` and `plan-*` options together, they are not mutually
exclusive.

`test-url` and `test-name`, or `plan-url` and `plan-name` are required.

### `/`

Returns ID of the created background task with additional metadata in JSON
and callback url for `/status` endpoint, returns the same in HTML format
if `format` is set to `html`.

  * `test-url` - URL of the repo test is located in - accepts a `string`
  * `test-ref` - Ref of the repository the test is located in - accepts
    a `string`, defaults to default branch of the repo
  * `test-path` - Points to directory where `fmf` tree is stored
  * `test-name` - Name of the test - accepts a `string`

  * `plan-url` - URL of the repo plan is located in - accepts a `string`
  * `plan-ref` - Ref of the repository the plan is located in - accepts
    a `string`, defaults to default branch of the repo
  * `plan-path` - Points to directory where `fmf` tree is stored
  * `plan-name` - Name of the plan - accepts a `string`

  * `format` - Format of the output - accepts a `string`, default is
    `json`, other options are `yaml`, `html` (serves as a basic
    human-readable output format)

### `/status`

Returns a status of the tmt object being processed by the backend.

  * `task_id` - ID of the task - accepts a `string`

### `/status/html`

Returns a status of the tmt object being processed by the backend in a
simple HTML formatting.

  * `task_id` - ID of the task - accepts a `string`

### `/health`

Returns a health status of the service.

## Attribution

The web interface design is based on the work of
[Fedora Design team](https://gitlab.com/fedora/design/team),
licensed under [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
The design elements include typography, color scheme, and visual
components adapted from the Fedora design guidelines.
