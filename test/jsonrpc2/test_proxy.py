# Copyright 2017 Matthijs Bos <matthijs_vlaarbos@hotmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import unittest.mock as mock

import fpgaedu.jsonrpc2

from fpgaedu.jsonrpc2 import Proxy

class ProxyTestCase(unittest.TestCase):
    def test_call(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": null
            }
        '''

        proxy = Proxy(mock_endpoint)
        result = proxy.call('method', params={'hello': 'world'})

        self.assertTrue(mock_endpoint.communicate.called)
        self.assertIsNone(result)

    def test_call_result(self):

        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'{"jsonrpc": "2.0", "id": 123, "result": 1}'
        proxy = Proxy(mock_endpoint)
        result = proxy.call('test')
        self.assertEqual(result, 1)

    def test_call_raises_server_error_request_parse_error(self):

        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0", 
                "id": 123, 
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
        '''
        proxy = Proxy(mock_endpoint)

        with self.assertRaises(fpgaedu.jsonrpc2.RequestParseError):
            proxy.call('test')

    def test_call_raises_server_error_invalid_request_error(self):

        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 1234,
                "error": {
                    "code": -32600,
                    "message": "Invalid request"
                }
            }
        '''

        proxy = Proxy(mock_endpoint)

        with self.assertRaises(fpgaedu.jsonrpc2.InvalidRequestError):
            proxy.call('method_name')

    def test_call_raises_server_error_unknown_method(self):

        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": "some_id_string",
                "error": {
                    "code": -32601,
                    "message": "Unknown method"
                }
            }
        '''

        proxy = Proxy(mock_endpoint)

        with self.assertRaises(fpgaedu.jsonrpc2.UnknownMethodError):
            proxy.call('test_method')

    def test_call_raises_server_error_invalid_params(self):

        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 12345,
                "error": {
                    "code": -32602,
                    "message": "Invalid params"
                }
            }
        '''

        proxy = Proxy(mock_endpoint)

        with self.assertRaises(fpgaedu.jsonrpc2.InvalidParamsError):
                proxy.call('test_method_trololo')

    def test_call_raises_server_error_internal_error(self):

        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 123456,
                "error": {
                    "code": -32603,
                    "message": "Internal error"
                }
            }
        '''

        proxy = Proxy(mock_endpoint)

        with self.assertRaises(fpgaedu.jsonrpc2.InternalServerError):
            proxy.call('test_method')
    
    def test_call_raises_server_error_unknown_code1(self):

        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 123,
                "error": {
                    "code": 0,
                    "message": "some error message",
                    "data": [1, 2, 3]
                }
            }
        '''

        proxy = Proxy(mock_endpoint)

        with self.assertRaises(fpgaedu.jsonrpc2.ServerError):
            try:
                proxy.call('test')
            except fpgaedu.jsonrpc2.ServerError as err:
                self.assertEqual(err.code, 0)
                self.assertEqual(err.message, "some error message")
                self.assertListEqual(err.data, [1, 2, 3])
                raise err

    def test_call_raises_server_error_unknown_code2(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 123,
                "error": {
                    "code": -999,
                    "message": "some error message two"
                }
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.ServerError):
            try:
                proxy.call('test')
            except fpgaedu.jsonrpc2.ServerError as err:
                self.assertEqual(err.code, -999)
                self.assertEqual(err.message, "some error message two")
                self.assertIsNone(err.data)
                raise err

    def test_call_raises_response_parse_error(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "some", "invalid", json
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.ResponseParseError):
            proxy.call('test_method_name')

    def test_call_raises_invalid_response_error1(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "id": 1,
                "result": null
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.InvalidResponseError):
            proxy.call('test_method')


    def test_call_raises_invalid_response_error2(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": 2.0,
                "id": 1,
                "result": null
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.InvalidResponseError):
            proxy.call('test_method')

    def test_call_raises_invalid_response_error3(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "result": null
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.InvalidResponseError):
            proxy.call('test_method')

    def test_call_raises_invalid_response_error4(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": {"must": "be null, number or string"},
                "result": null
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.InvalidResponseError):
            proxy.call('test_method')

    def test_call_raises_invalid_response_error5(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 1
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.InvalidResponseError):
            proxy.call('test_method')

    def test_call_raises_invalid_response_error6(self):
        mock_endpoint = mock.Mock()
        mock_endpoint.communicate.return_value = b'''
            {
                "jsonrpc": "2.0",
                "id": 1, 
                "result": null,
                "error": {
                    "code": 1,
                    "message": "Invalid response"
                }
            }
        '''
        proxy = Proxy(mock_endpoint)
        with self.assertRaises(fpgaedu.jsonrpc2.InvalidResponseError):
            proxy.call('test_method')

    # def test_call_raises_invalid_response_error7(self):
    #     mock_endpoint = mock.Mock()
    #     mock_endpoint.communicate.return_value = '''
    #         {
    #             "jsonrpc": "2.0",
    #             "id": null, 
    #             "error": { }
    #         }
    #     '''
    #     proxy = Proxy(mock_endpoint)
    #     with self.assertRaises(fpgaedu.jsonrpc2.InvalidResponseError):
    #         proxy.call('test_method')

    