import logging

from argo_probe_eosccore_recommender.nagios_response import *

LOGGER = logging.getLogger("eosccore-recommender-probe")

# A graph that represents how the status of a component
# is dependent on the status of other components
status_dependency_graph = {
    "Nearline engine": ["Preprocessor"],
    "Preprocessor": ["JMS"],
    "Online Engine": ["Nearest neighbor finder"]
}


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


def global_status_check(response_json):
    """
    Check the global status of the service

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


def specific_component_status_check(component):
    """
    Returns a clojure that checks the status of the specified component.
    First it will try to check all the components in the dependency graph
    of the parent component recursively.

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
    elif component == "Provider_insights":
        component = "Provider insights"
    elif component == "Nearline_engine":
        component = "Nearline engine"
    elif component == "Nearest_neighbor_finder_training_module":
        component = "Nearest neighbor finder training module"
    elif component == "Nearest_neighbor_finder":
        component = "Nearest neighbor finder"

    def _check_dependencies_statuses(response_json):
        # fetch the dependencies of the component
        if component in status_dependency_graph:
            dependencies = status_dependency_graph[component]
            for dep in dependencies:
                logging.debug(f"Recursively checking dependency {dep} of component {component}. . .")
                dep_status = specific_component_status_check(dep)(response_json)
                if not dep_status.is_ok():
                    logging.debug(f"Error while checking dependency {dep} of component {component}. . .")
                    return critical(f"Dependency check failed for {component}.{dep_status.message}")

        return ok(f"Component {component} dependencies are ok.")

    def _check_component_status(response_json):
        """
        Clojure that encapsulates a component and performs checks on the response for the
        given component.

        :param response_json: Rs json response
        :return: NagiosResponse
        """
        # check if the component name exists in the json response
        LOGGER.debug(f"Checking component {component} . . .")
        if component not in response_json:
            LOGGER.debug(f"Did not find component:{component} in the response. {str(response_json)}")
            return critical(f"Component {component} was not found in the response.")

        # check that the specified component has status field declared
        if "status" not in response_json[component]:
            LOGGER.debug(f"Component {component} status field was not found in the response. {str(response_json)}")
            return critical(f"Component {component} status field was not found in the response.")

        # check that the status of the specified component is UP
        if response_json[component]["status"] != "UP":
            return critical(f"Status for the {component} component is {response_json[component]['status']}.")

        return ok(f"Component {component} is UP.")

    def _status_check(response_json):
        dep_status = _check_dependencies_statuses(response_json)
        if not dep_status.is_ok():
            return dep_status
        return _check_component_status(response_json)

    return _status_check
