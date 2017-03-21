import unittest
import unittest.mock as mock

import fpgaedu.jsonrpc2

class TcpSocketEndpointTestCase(unittest.TestCase):

    @mock.patch('socket.create_connection')
    def test_communicate_raises_endpoint_error(self, mock_create_connection):

        mock_create_connection.side_effect = OSError

        endpoint = fpgaedu.jsonrpc2.TcpSocketEndpoint('localhost', 12345)

        with self.assertRaises(fpgaedu.jsonrpc2.EndpointError):
            endpoint.communicate('test')

    @mock.patch('socket.create_connection')
    def test_communicate(self, mock_create_connection):

        mock_socket = mock.Mock()
        mock_socket.__enter__ = mock.Mock(return_value=mock_socket)
        mock_socket.__exit__ = mock.Mock(return_value=False)
        mock_socket.recv.side_effect = ([b'test response', ''])
        mock_create_connection.return_value = mock_socket

        endpoint = fpgaedu.jsonrpc2.TcpSocketEndpoint('localhost', 12345)

        response = endpoint.communicate(b'test request')

        self.assertEqual(response, b'test response')
