import base64
import glob
import os
import random
import shutil
import subprocess
import time
import xml.etree.ElementTree as et

import psutil

import fpgaedu.jsonrpc2

DEFAULT_LINUX = '/opt/Xilinx'
DEFAULT_WINDOWS = r'C:\Xilinx'
USER_SETTINGS_LINUX = os.path.expanduser('~/.Xilinx/')
USER_SETTINGS_WINDOWS = os.path.expanduser(r'~\AppData\Roaming\Xilinx')

def locate():
    '''
    Attempts to find a vivado executable. First attempts to find the executable
    that corresponds to the PATH's vivado command. If this is not set, the
    Xilinx user settings directory's registry/installedSW.xml file is checked
    for references to existing installations. If this file does not contain
    usable references, Xilinx's default locations are checked for vivado
    installations. These are /opt/Xilinx and C:\\Xilinx for Linux and Windows
    respectively.

    The function returns the path to a vivado executable or None if no
    executable is found.
    '''

    # If the vivado executable is available from the current PATH, then
    # return the path to that executable.
    path_vivado = shutil.which('vivado')
    if path_vivado:
        return path_vivado

    # Set variables based on the os type.
    if os.name == 'posix':
        user_settings = USER_SETTINGS_LINUX
        install_dirs = {DEFAULT_LINUX}
    elif os.name == 'nt':
        user_settings = USER_SETTINGS_WINDOWS
        install_dirs = {DEFAULT_WINDOWS}
    else:
        raise Exception('invalid os %s' % os.name)

    # Look in the xilinx user settings installedSW.xml file for Xilinx
    # installation directories.
    if os.path.exists(user_settings):
        installed_sw = os.path.join(user_settings, 'registry', 'installedSW.xml')
        installed_sw_xml = et.parse(installed_sw)
        # Add every <installedPath> tag's contents to the set of Xilinx
        # installation directories.
        for element in installed_sw_xml.getroot().findall('*/installedPath'):
            install_dirs.add(element.text)

    # Look for vivado installations in every Xilinx installation directory.
    # Assuming that every vivado installation is following the convention:
    # [XIL DIR]/Vivado/[VERSION]/bin/vivado
    vivado_paths = set()
    for install_dir in install_dirs:
        glob_pattern = os.path.join(install_dir, 'Vivado', '*', 'bin', 'vivado')
        matches = glob.glob(glob_pattern)
        vivado_paths.union(set(matches))

    if len(vivado_paths) == 0:
        return None
    else:
        return vivado_paths.pop()

class SessionTimeoutError(Exception):
    """
    Class indicating a timeout condition.
    """
    pass

class Session:
    """
    Wrapper class that abstracts management of and interaction with a vivado
    process in which a server application is executed, allowing for interprocess
    communication between this class' process and Vivado's functionality.
    """
    def __init__(self, server_port=3742):
        self._server_port = server_port
        self._vivado_path = locate()
        self._process = None
        self._child_processes = []
        self._tcl_init_script = os.path.join(os.path.dirname(__file__), 'tcl', 'start.tcl')
        self._rpc_endpoint = fpgaedu.jsonrpc2.TcpSocketEndpoint('localhost', server_port)
        self._rpc_proxy = fpgaedu.jsonrpc2.Proxy(self._rpc_endpoint)

    @property
    def server_port(self):
        return self._server_port

    def start(self, timeout=30):
        """
        Start the Vivado session. A SessionTimeoutError is raised if the
        specified timeout period has passed.
        """
        args = [self._vivado_path, '-mode', 'batch', '-nolog', '-nojournal',
                '-notrace', '-source', self._tcl_init_script]

        self._process = psutil.Popen(args, shell=False)

        for _ in range(max(1, int(timeout))):
            try:
                self.echo()
                return
            except fpgaedu.jsonrpc2.RpcError:
                time.sleep(1)
                continue
        
        self.stop()

        raise SessionTimeoutError

    def stop(self):
        """
        Stops this session's Vivado process by killing the current process
        and all child processes.
        """
        if self._process is not None:
            # Code derived from http://stackoverflow.com/a/4229404
            parent_proc = psutil.Process(self._process.pid)
            child_procs = parent_proc.children(recursive=True)
            for child_proc in child_procs:
                child_proc.kill()
            psutil.wait_procs(child_procs)
            parent_proc.kill()
            parent_proc.wait()
            self._process = None

    def __del__(self):
        self.stop()

    def echo(self):
        """
        Test the availability of the server application.
        """
        echo_params = {'echo': random.randint(0, 999)}
        echo_result = self._rpc_proxy.call('echo', params=echo_params)
        if echo_params != echo_result:
            raise AssertionError

    def program(self, target, device, bitstream):
        """
        Program a board's fpga using the provided bitstream.
        """
        bitstream_base64 = base64.b64encode(bitstream)

        program_params = {
            'target': target,
            'device': device,
            'bitstream': bitstream_base64.decode()
        }

        self._rpc_proxy.call('program', params=program_params)

    def get_target_identifiers(self):
        return self._rpc_proxy.call('getTargetIdentifiers')

    def get_device_identifiers(self, target_identifier):

        params = {
            'targetIdentifier': target_identifier
        }
        return self._rpc_proxy.call('getDeviceIdentifiers', params=params)