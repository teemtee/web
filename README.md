# web
Web app for checking tmt tests, plans and stories
# Run instructions
To run the service locally for development purposes, use the following command:
```bash
docker-compose up --build
```
## Tests
To run the tests, use the `pytest` command
## Environment variables
`REDIS_URL` - optional, passed to Celery on initialization as a `broker` and `backend` argument,
default value is `redis://localhost:6379`

`CLONE_DIR_PATH` - optional, specifies the path where the repositories will be cloned, default value is `./.repos/`

`USE_CELERY` - optional, specifies if the app should use Celery, set to `false` for running without Celery

`API_HOSTNAME` - required, specifies the hostname of the API, used for creating the callback URL to the service
