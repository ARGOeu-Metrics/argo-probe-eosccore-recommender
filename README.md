# argo-probe-eosccore-recommender

A new probe that checks the different components of the recommender service

# Checks

The probe executes checks against
the following expected functionalities.

- The response of the given url is a `200` status code.
- The response body is valid json.
- The top-level `status` field is present and has the value of `UP`.
- The given(optional) `component` is present in the json and its nested `status` field has the value of `UP`. 

# Arguments

Probe command line arguments.

- `--host, -H` The endpoint where the rs status response exists.
- `--timeout, -t` The timeout duration in seconds for the http call.
- `--verify` Verify ssl certificate of the endpoint.
- `--component, -c` Specific component to check.
- `--verbose, -vvv` For maximum log output.

# Run
```shell
$ ./check_rs.py --host http://rs.io --timeout 60 --component JMS --verify
```