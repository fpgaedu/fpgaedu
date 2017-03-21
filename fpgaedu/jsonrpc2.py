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

import json
import socket

import jsonschema

CODE_PARSE_ERROR = -32700
CODE_INVALID_REQUEST = -32600
CODE_UNKNOWN_METHOD = -32601
CODE_INVALID_PARAMS = -32602
CODE_INTERNAL_ERROR = -32603
REQUEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "A JSON RPC 2.0 request",
    "oneOf": [
        {
            "description": "An individual request",
            "$ref": "#/definitions/request"
        },
        {
            "description": "An array of requests",
            "type": "array",
            "items": {"$ref": "#/definitions/request"}
        }
    ],
    "definitions": {
        "request": {
            "type": "object",
            "required": ["jsonrpc", "method"],
            "properties": {
                "jsonrpc": {"enum": ["2.0"]},
                "method": {
                    "type": "string"
                },
                "id": {
                    "type": ["string", "number", "null"],
                    "note": [
                        "While allowed, null should be avoided: "\
                            "http://www.jsonrpc.org/specification#id1",
                        "While allowed, a number with a fractional part " \
                            "should be avoided: http://www.jsonrpc.org/specification#id2"
                    ]
                },
                "params": {
                    "type": ["array", "object"]
                }
            }
        }
    }
}
RESPONSE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "A JSON RPC 2.0 response",
    "oneOf": [
        {"$ref": "#/definitions/success"},
        {"$ref": "#/definitions/error"},
        {
            "type": "array",
            "items": {
                "oneOf": [
                    {"$ref": "#/definitions/success"},
                    {"$ref": "#/definitions/error"}
                ]
            }
        }
    ],
    "definitions": {
        "common": {
            "required": ["id", "jsonrpc"],
            "not": {
                "description": "cannot have result and error at the same time",
                "required": ["result", "error"]
            },
            "type": "object",
            "properties": {
                "id": {
                    "type": ["string", "integer", "null"],
                    "note": [
                        "spec says a number which should not contain a fractional part",
                        "We choose integer here, but this is unenforceable with some languages"
                    ]
                },
                "jsonrpc": {"enum": ["2.0"]}
            }
        },
        "success": {
            "description": "A success. The result member is then required and can be anything.",
            "allOf": [
                {"$ref": "#/definitions/common"},
                {"required": ["result"]}
            ]
        },
        "error": {
            "allOf" : [
                {"$ref": "#/definitions/common"},
                {
                    "required": ["error"],
                    "properties": {
                        "error": {
                            "type": "object",
                            "required": ["code", "message"],
                            "properties": {
                                "code": {
                                    "type": "integer",
                                    "note": ["unenforceable in some languages"]
                                },
                                "message": {"type": "string"},
                                "data": {
                                    "description": "optional, can be anything"
                                }
                            }
                        }
                    }
                }
            ]
        }
    }
}

class RpcError(Exception):
    pass

class ServerError(RpcError):
    """
    Error class representing the case in which an error is encountered during
    the processon of a JSON-RPC request on the server.
    """
    def __init__(self, code, message, data=None):
        super().__init__(code, message, data)
        self.code = code
        self.message = message
        self.data = data

class RequestParseError(ServerError):
    """
    Error class representing the case in which invalid JSON was received by the
    server.
    """
    def __init__(self, message, data=None):
        super().__init__(CODE_PARSE_ERROR, message, data=data)

class InvalidRequestError(ServerError):
    def __init__(self, message, data=None):
        super().__init__(CODE_INVALID_REQUEST, message, data=data)

class UnknownMethodError(ServerError):
    def __init__(self, message, data=None):
        super().__init__(CODE_UNKNOWN_METHOD, message, data=data)

class InvalidParamsError(ServerError):
    def __init__(self, message, data=None):
        super().__init__(CODE_INVALID_PARAMS, message, data=data)

class InternalServerError(ServerError):
    def __init__(self, message, data=None):
        super().__init__(CODE_INTERNAL_ERROR, message, data=data)

class ResponseParseError(RpcError):
    pass

class InvalidResponseError(RpcError):
    pass

class EndpointError(RpcError):
    pass

class Proxy:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self._id = 0

    def call(self, method, params=None):

        self._id += 1

        request = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
        }

        if params is not None:
            request["params"] = params

        jsonschema.validate(request, REQUEST_SCHEMA)

        request_json = json.dumps(request).encode()
        # Transmit request json and receive response through endpoint
        response_json = self.endpoint.communicate(request_json)
        # Parse response
        try:
            response = json.loads(response_json.decode())
        except json.JSONDecodeError as err:
            raise ResponseParseError from err
        # Validate response
        try:
            jsonschema.validate(response, RESPONSE_SCHEMA)
        except jsonschema.ValidationError:
            raise InvalidResponseError

        try:
            return response['result']
        except KeyError:
            error_code = response['error'].get('code')
            error_message = response['error'].get('message')
            error_data = response['error'].get('data')

            if error_code == CODE_PARSE_ERROR:
                raise RequestParseError(error_message, data=error_data)
            elif error_code == CODE_INVALID_REQUEST:
                raise InvalidRequestError(error_message, data=error_data)
            elif error_code == CODE_UNKNOWN_METHOD:
                raise UnknownMethodError(error_message, data=error_data)
            elif error_code == CODE_INVALID_PARAMS:
                raise InvalidParamsError(error_message, data=error_data)
            elif error_code == CODE_INTERNAL_ERROR:
                raise InternalServerError(error_message, data=error_data)
            else:
                raise ServerError(error_code, error_message, error_data)

class TcpSocketEndpoint:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def communicate(self, data):
        try:
            with socket.create_connection((self.host, self.port)) as sock:
                sock.sendall(data)
                sock.shutdown(socket.SHUT_WR)
                recv_data = b''
                while True:
                    packet = sock.recv(1024)
                    if not packet:
                        break
                    recv_data += packet
                return recv_data
        except OSError as err:
            raise EndpointError from err

