# web
Web app for checking tmt tests, plans and stories
# API
API for checking tmt tests and plans metadata
* `/`
  * `test-url` - URL of the repo test is located in - accepts a `string`
  * `test-name` - Name of the test - accepts a `string`
  * `test-ref` - Ref of the repository the test is located in - accepts a `string`, defaults to default branch of the repo
  * `test-path` - Points to directory where `fmf` tree is stored
  * `plan-url` - URL of the repo plan is located in - accepts a `string`
  * `plan-name` - Name of the plan - accepts a `string`
  * `plan-ref` - Ref of the repository the plan is located in - accepts a `string`, defaults to default branch of the repo
  * `plan-path` - Points to directory where `fmf` tree is stored
  * `format` - Format of the output - accepts a `string`, default is `json`, other options are `xml`, `html` (serves as a basic human-readable output format)

If we want to display metadata for both tests and plans, we can combine the `test-*`
and `plan-*` options together, they are not mutually exclusive.

If we use `url` and `name` options, we have to provide both of them.