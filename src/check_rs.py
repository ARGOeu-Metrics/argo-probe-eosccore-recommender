#!/usr/bin/python3
from json import JSONDecodeError

import requests
import logging.handlers
import sys
import argparse

from argo_probe_eosccore_recommender.nagios_response import *

# set up logging

LOGGER = logging.getLogger("eosccore-recommender-probe")


def apply_status_check(response_json):
    """
    Check the generic status of the service

    :param response_json: Rs json response
    :return: NagiosResponse
    """
    LOGGER.debug(f"Checking service status . . .")
    if "status" not in response_json:
        LOGGER.error(f"status field was not found in the response. {str(response_json)}")
        return critical("Status field was not found in the response.")

    if response_json["status"] != "UP":
        return critical(f"Status is {response_json['status']} instead of UP.")

    return ok("Service is UP.")


def apply_specific_component_check(component):
    """
    Returns a clojure that checks the status of the specified component

    :param component:
    :return: NagiosResponse
    """
    # translate the names of components to avoid spaces 
    if component == "Marketplace_RS":
        component = "Marketplace RS"
    elif component == "Athena_RS":
        component = "Athena RS"
    elif component == "Online_engine":
        component = "Online engine"
        
    def check_component(response_json):
        """
        Clojure that encapsulates a component and performs checks on the response for the
        given component.

        :param response_json: Rs json response
        :return: NagiosResponse
        """
        # check if the component name exists in the json response
        LOGGER.debug(f"Checking component {component} . . .")
        if component not in response_json:
            LOGGER.error(f"Did not find component:{component} in the response. {str(response_json)}")
            return critical(f"Component {component} was not found in the response.")

        # check that the specified component has status field declared
        if "status" not in response_json[component]:
            LOGGER.error(f"Component {component} status field was not found in the response. {str(response_json)}")
            return critical(f"Component {component} status field was not found in the response.")

        # check that the status of the specified component is UP
        if response_json[component]["status"] != "UP":
            return critical(f"Status for the {component} component is {response_json[component]['status']}.")

        return ok(f"Component {component} is UP.")

    return check_component


def apply_response_checks(response_json, *checks):
    """
    Accepts a list of functions that perform response checks.
    Each check function accepts a response_json and returns a NagiosResponse

    :param response_json: a rs json response
    :param checks: functions that perform checks on a rs json response and return NagiosResponse
    :return: NagiosResponse containing the first encountered error otherwise last success
    """
    nagios_response = unknown("No checks applied.")
    # apply one by one the checks
    for checkF in checks:
        nagios_response = checkF(response_json)
        # if a check is not ok, cancel early and report the error
        if not nagios_response.is_ok():
            break

    return nagios_response


def check(args):
    """
    Calls the rs endpoint to retrieve the status of the service(s) and sets up the execution check flow.

    :param args: command line arguments
    :return: final NagiosResponse after the execution of the check flow
    """
    LOGGER.debug(f"Accessing url: {args.url} . . .")
    try:
        rs_response = requests.get(
            url=args.url,
            verify=args.verify,
            timeout=args.timeout
        )
        LOGGER.debug(
            f"URL {args.url} answered with a status code of"
            f" {rs_response.status_code} and body of {rs_response.content}")
        if rs_response.status_code == 200:
            # set up the check functions
            checks = []
            if args.component is not None:
                checks.append(apply_specific_component_check(component=args.component))
            else:
                checks.append(apply_status_check)
            return apply_response_checks(rs_response.json(), *checks)

        LOGGER.error(f"Response status code was {rs_response.status_code}. {str(rs_response.json())}")
        return critical(f"Response status code was {rs_response.status_code}. {str(rs_response.json())}")

    except JSONDecodeError as jsone:
        return critical(f"Could not parse json response. {str(jsone)}")
    except Exception as e:
        return critical(f"Exception occurred. {str(e)}")


def main(args):
    nagios_response = check(args)
    print(nagios_response.message)
    sys.exit(nagios_response.code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("EOSCCORE RECOMMENDER PROBE")

    parser.add_argument(
        "-H", "--host", dest="host", type=str, 
        help="RS host"
    )
    parser.add_argument(
        "-u", "--url", dest="url", type=str, required=True,
        help="RS status url"
    )
    parser.add_argument(
        "-c", "--component", dest="component", type=str,
        help="Specific component to check"
    )

    parser.add_argument(
        "-t", "--timeout", dest="timeout", type=int,
        default=60, help="timeout"
    )

    parser.add_argument(
        "--verify", dest="verify", action="store_true",
        help="SSL verification for requests"
    )

    parser.add_argument(
        "-vvv", "--verbose", dest="verbose", action="store_true",
        help="Verbose logging"
    )

    arguments = parser.parse_args()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s[%(process)d]: %(levelname)s - %(message)s'))
    LOGGER.addHandler(console_handler)
    if arguments.verbose:
        import http.client

        http.client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    sys.exit(main(args=arguments))
