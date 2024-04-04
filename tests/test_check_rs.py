import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch

from modules.nagios_response import *
from src.check_rs import *
from modules.checks import *


class RsCheckTestCase(unittest.TestCase):

    def mocked_requests_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
                self.content = ""

            def json(self):
                if self.status_code == 500:
                    raise JSONDecodeError("error", "doc", 0)
                return self.json_data

        if kwargs["url"] == 'http://ex.com/500':
            return MockResponse({}, 500)
        if kwargs["url"] == 'http://ex.com/400':
            return MockResponse({"bad": "request"}, 400)
        elif kwargs["url"] == 'http://ex.com/200':
            return MockResponse({
                "status": "UP",
                "kafka": {
                    "status": "UP"
                }
            }, 200)

        return MockResponse(None, 404)

    @patch("requests.get", side_effect=mocked_requests_get)
    def test_check_component_status(self, mock_requests):
        nr = check(Namespace(url="http://ex.com/200", verify=True, timeout=60, component="kafka"))
        self.assertEqual("OK - Component kafka is UP.", nr.__str__())
        self.assertEqual(0, nr.code)
        self.assertTrue(nr.is_ok())

    @patch("requests.get", side_effect=mocked_requests_get)
    def test_check_status(self, mock_requests):
        nr = check(Namespace(url="http://ex.com/200", verify=True, timeout=60, component=None))
        self.assertEqual("OK - Service is UP.", nr.__str__())
        self.assertEqual(0, nr.code)
        self.assertTrue(nr.is_ok())

    @patch("requests.get", side_effect=mocked_requests_get)
    def test_check_status_all(self, mock_requests):
        nr = check(Namespace(url="http://ex.com/200", verify=True, timeout=60, component="all"))
        self.assertEqual("OK - Service is UP.", nr.__str__())
        self.assertEqual(0, nr.code)
        self.assertTrue(nr.is_ok())

    @patch("requests.get", side_effect=mocked_requests_get)
    def test_check_json_decode_exception_raised(self, mock_requests):
        nr = check(Namespace(url="http://ex.com/500", verify=True, timeout=60))
        self.assertEqual("CRITICAL - Could not parse json response. error: line 1 column 1 (char 0)", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    @patch.object(requests, 'get', MagicMock(side_effect=Exception("side-effect")))
    def test_check_exception_raised(self):
        nr = check(Namespace(url="http://ex.com", verify=True, timeout=60))
        self.assertEqual("CRITICAL - Exception occurred. "
                         "side-effect", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    @patch("requests.get", side_effect=mocked_requests_get)
    def test_check_error_status_code(self, mock_requests):
        nr = check(Namespace(url="http://ex.com/400", verify=True, timeout=60))
        self.assertEqual("CRITICAL - Response status code was 400. {'bad': 'request'}", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_apply_response_checks_return_error(self):
        rj = {
            "status": "down",
            "kafka": {
                "status": "UP"
            }
        }

        nr = apply_response_checks(rj, global_status_check, specific_component_status_check("kafka"))
        self.assertEqual("CRITICAL - Status is down instead of UP.", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_apply_response_checks_unknown(self):
        nr = apply_response_checks(response_json={})
        self.assertEqual("UNKNOWN - No checks applied.", nr.__str__())
        self.assertEqual(3, nr.code)
        self.assertFalse(nr.is_ok())

    def test_apply_response_checks_return_last_success(self):
        rj = {
            "status": "UP",
            "kafka": {
                "status": "UP"
            }
        }

        nr = apply_response_checks(rj, global_status_check, specific_component_status_check("kafka"))
        self.assertEqual("OK - Component kafka is UP.", nr.__str__())
        self.assertEqual(0, nr.code)
        self.assertTrue(nr.is_ok())

    def test_specific_component_status_check_status_not_up_depth_2(self):
        f = specific_component_status_check("Preprocessor")
        nr = f(response_json={"Preprocessor": {"status": "UP"}, "JMS": {"status": "DOWN"}})
        self.assertEqual("CRITICAL - Dependency check failed for Preprocessor.Status for the JMS component is DOWN.",
                         nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_specific_component_status_check_status_not_up_depth_3(self):
        f = specific_component_status_check("Nearline_engine")
        nr = f(response_json={"Nearline engine": {"status": "UP"}, "Preprocessor": {"status": "UP"},
                              "JMS": {"status": "DOWN"}})
        self.assertEqual(
            "CRITICAL - Dependency check failed for Nearline engine."
            "Dependency check failed for Preprocessor."
            "Status for the JMS component is DOWN.",
            nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_specific_component_status_check_status_not_up(self):
        f = specific_component_status_check("kafka")
        nr = f(response_json={"kafka": {"status": "down"}})
        self.assertEqual("CRITICAL - Status for the kafka component is down.", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_specific_component_status_check_status_not_found(self):
        f = specific_component_status_check("kafka")
        nr = f(response_json={"kafka": {"unknown": "down"}})
        self.assertEqual("CRITICAL - Component kafka status field was not found in the response.", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_specific_component_status_check_not_found(self):
        f = specific_component_status_check("unknown")
        nr = f(response_json={"kafka": {"status": "UP"}})
        self.assertEqual("CRITICAL - Component unknown was not found in the response.", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_specific_component_status_check(self):
        f = specific_component_status_check("kafka")
        nr = f(response_json={"kafka": {"status": "UP"}})
        self.assertEqual("OK - Component kafka is UP.", nr.__str__())
        self.assertEqual(0, nr.code)
        self.assertTrue(nr.is_ok())

    def test_global_status_check_no_status_field(self):
        nr = global_status_check(response_json={"no": "field"})
        self.assertEqual("CRITICAL - Status field was not found in the response.", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_global_status_check_not_up(self):
        nr = global_status_check(response_json={"status": "down"})
        self.assertEqual("CRITICAL - Status is down instead of UP.", nr.__str__())
        self.assertEqual(2, nr.code)
        self.assertFalse(nr.is_ok())

    def test_global_status_check(self):
        nr = global_status_check(response_json={"status": "UP"})
        self.assertEqual("OK - Service is UP.", nr.__str__())
        self.assertEqual(0, nr.code)
        self.assertTrue(nr.is_ok())

    def test_warming_nagios_response(self):
        warning_nagios_response = warning("w")
        self.assertEqual("WARNING - w", warning_nagios_response.__str__())
        self.assertEqual(1, warning_nagios_response.code)
        self.assertFalse(warning_nagios_response.is_ok())

    def test_critical_nagios_response(self):
        critical_nagios_response = critical("c")
        self.assertEqual("CRITICAL - c", critical_nagios_response.__str__())
        self.assertEqual(2, critical_nagios_response.code)
        self.assertFalse(critical_nagios_response.is_ok())

    def test_unknown_nagios_response(self):
        unknown_nagios_response = unknown("u")
        self.assertEqual("UNKNOWN - u", unknown_nagios_response.__str__())
        self.assertEqual(3, unknown_nagios_response.code)
        self.assertFalse(unknown_nagios_response.is_ok())

    def test_ok_nagios_response(self):
        ok_nagios_response = ok("ok")
        self.assertEqual("OK - ok", ok_nagios_response.__str__())
        self.assertEqual(0, ok_nagios_response.code)
        self.assertTrue(ok_nagios_response.is_ok())


if __name__ == '__main__':
    unittest.main()
