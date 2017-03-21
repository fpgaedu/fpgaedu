import os.path
import unittest
import unittest.mock as mock

import psutil
import pytest

import fpgaedu.vivado

def find_vivado_pids():
    '''
    return a set containing the pids for the vivado processes currently
    activated.
    '''
    vivado_procs = filter(lambda p: 'vivado' in p.name(), psutil.process_iter())
    return {p.pid for p in vivado_procs}

class SessionTestCase(unittest.TestCase):

    def test_init_tcl_init_script_exists(self):
        session = fpgaedu.vivado.Session()
        self.assertTrue(os.path.exists(session._vivado_path))
        self.assertTrue(os.path.exists(session._tcl_init_script))

    def test_init_server_port_property(self):
        session = fpgaedu.vivado.Session(server_port=99999)
        self.assertEqual(session.server_port, 99999)

    @pytest.mark.timeout(2)
    def test_start_timeout(self):
        '''
        Ensure timeout works and that any spawned process isdestroyed afterwards
        '''
        pids_before = find_vivado_pids()

        session = fpgaedu.vivado.Session()
        session._rpc_proxy = mock.Mock()
        session._rpc_proxy.call.side_effect = fpgaedu.jsonrpc2.EndpointError

        with self.assertRaises(fpgaedu.vivado.SessionTimeoutError):
            session.start(timeout=1)

        pids_after = find_vivado_pids()

        self.assertEqual(len(pids_before - pids_after), 0)


    @pytest.mark.timeout(60)
    def test_start(self):

        pids_before = find_vivado_pids()

        session = fpgaedu.vivado.Session()
        session.start(timeout=60)

        session_pids = find_vivado_pids() - pids_before
        # vivado process and a child process that was created in sourcing the
        # server script.
        self.assertGreaterEqual(len(session_pids), 1)

        session.stop()

        self.assertTrue(find_vivado_pids().isdisjoint(session_pids))

    @mock.patch('random.randint')
    def test_echo(self, mock_randint):

        mock_randint.return_value = 12345

        session = fpgaedu.vivado.Session()
        session._rpc_proxy = mock.Mock()
        session._rpc_proxy.call = mock.Mock(return_value={"echo": 12345})

        session.echo()

        session._rpc_proxy.call.assert_called_with('echo', params={"echo": 12345})

    def test_echo_raises(self):

        session = fpgaedu.vivado.Session()
        session._rpc_proxy = mock.Mock()
        session._rpc_proxy.call.return_value = None

        with self.assertRaises(AssertionError):
            session.echo()

    def test_program(self):

        session = fpgaedu.vivado.Session()
        session.start()

        target = session.get_target_identifiers()[0]
        device = session.get_device_identifiers(target)[0]
        
        with open("/home/matthijsbos/Dropbox/fpgaedu/python/fpgaedu/fpgaedu/tcl/test/resources/nexys4.bit", 'rb') as f:
            bitstream_data = f.read()
        
        session.program(target, device, bitstream_data)