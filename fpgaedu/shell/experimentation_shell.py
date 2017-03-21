import cmd

class ExperimentationShell(cmd.Cmd):
    '''
    Custom shell implementation based on cmd.Cmd that allows for dynamic
    loading of commands.
    '''

    def __init__(self):
        super().__init__()
        self.commands = {}

    def do_exit(self, _):
        '''
        Handler for exit shell command.
        '''
        return True

    def default(self, line):
        argv = line.split()

        if len(argv) <= 0:
            super().default(line)
            return

        if argv[0] in self.commands:
            try:
                self.commands[argv[0]].execute(argv)
            except SystemExit:
                pass
        else:
            super().default(line)
