#!/usr/bin/python3
from json import JSONDecodeError

import requests
import sys
import argparse

from modules.checks import *

# set up logging

LOGGER = logging.getLogger("eosccore-recommender-probe")


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
            checks = [global_status_check]
            if args.component is not None and args.component != "all":
                checks.append(specific_component_status_check(component=args.component))

            return apply_response_checks(rs_response.json(), *checks)

        LOGGER.debug(f"Response status code was {rs_response.status_code}. {str(rs_response.json())}")
        return critical(f"Response status code was {rs_response.status_code}. {str(rs_response.json())}")

    except JSONDecodeError as jsone:
        return critical(f"Could not parse json response. {str(jsone)}")
    except Exception as e:
        return critical(f"Exception occurred. {str(e)}")


def main(args):
    nagios_response = check(args)
    print(nagios_response)
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
