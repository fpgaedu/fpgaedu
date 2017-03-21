import argparse


class ProgramCommand:

    name = 'program'
    description = 'program a board'

    parser = argparse.ArgumentParser(name, description=description)
    parser.add_argument('bitstream',
                        help='the bitstream used for programming',
                        metavar='BITSTREAM')
    parser.add_argument('target',
                        help='the target identifier',
                        metavar="TARGET")
    parser.add_argument('device',
                        help='the device identifier',
                        metavar='DEVICE')

    def __init__(self):
        self.programmer = None

    def execute(self, argv):

        options = ProgramCommand.parser.parse_args(argv[1:])

        print('Programming')
        print('   bitstream = %s' % options.bitstream)
        print('   target    = %s' % options.target)
        print('   device    = %s' % options.device)
