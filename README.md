# web
Web app for checking tmt tests, plans and stories
# API
API for checking tmt tests and plans metadata
* `/`
  * `test_url` - URL of the repo test is located in - accepts a `string`
  * `test_name` - Name of the test - accepts a `string`
  * `test_ref` - Ref of the repository the test is located in - accepts a `string`, default is `main`
  * `plan_url` - URL of the repo plan is located in - accepts a `string`
  * `plan_name` - Name of the plan - accepts a `string`
  * `plan_ref` - Ref of the repository the plan is located in - accepts a `string`, default is `main`

If we want to display metadata for both tests and plans, we can combine the `test_*`
and `plan_*` options together, they are not mutually exclusive.

If we use `*_url` and `*_name` options, we have to provide both of them.