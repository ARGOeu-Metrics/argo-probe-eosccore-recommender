# argo-probe-eosccore-recommender

A new probe that checks the different components of the recommender service

# Checks

The probe executes checks against
the following expected functionalities.

- The response of the given url is a `200` status code.
- The response body is valid json.
- The top-level `status` field is present and has the value of `UP`.
- The given(optional) `component` is present in the json and its nested `status` field has the value of `UP`.
- If the component is given, we also check recursively the components it depends on.

# Arguments

Probe command line arguments.

- `--host, -H` The Hostname of the service.
- `--url, -u` The endpoint where the rs status response exists.
- `--timeout, -t` The timeout duration in seconds for the http call.
- `--verify` Verify ssl certificate of the endpoint.
- `--component, -c` Specific component to check.
  The argument can be omitted or be provided with the value of `all`
  to only check the global status of the service.
- `--verbose, -vvv` For maximum log output.

# Run

```shell
$ ./check_rs.py --url http://rs.io/status --timeout 60 --component JMS --verify
```
