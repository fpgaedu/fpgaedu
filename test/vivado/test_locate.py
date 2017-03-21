
import os
import unittest
import unittest.mock as mock
import xml.etree.ElementTree as et
import fpgaedu.vivado

curr_dir = os.path.dirname(__file__)
installedSW1 = et.parse(os.path.join(curr_dir, 'resources', 'installedSW1.xml'))

class LocateTestCase(unittest.TestCase):

    @mock.patch("shutil.which")
    def test_locate_path(self, mock_which):
        # Initialize
        mock_which.return_value = 'some/test/directory/to/executable'
        # Call
        location = fpgaedu.vivado.locate()
        # Assert
        mock_which.assert_called_with('vivado')
        # self.assertEqual(location, 'some/test/directory/to/executable')

    @mock.patch("os.name", 'posix')
    @mock.patch("xml.etree.ElementTree.parse")
    @mock.patch("shutil.which")
    def test_locate_from_user_settings(self, mock_which, mock_parse):
        # Initialize
        mock_which.return_value = None
        mock_parse.return_value = installedSW1
        # Call
        location = fpgaedu.vivado.locate()
        # Assert
        mock_which.assert_called_with('vivado')
        mock_parse.assert_called_with(os.path.expanduser('~/.Xilinx/registry/installedSW.xml'))
        # xilinx_installed_sw_path = os.path.join('~', '.Xilinx', 'registry',
        #                                         'installedSW.xml')

        # self.assertEqual(location, "/home/matthijsbos/Xilinx/Vivado/2016.4/bin/vivado")

