
import argparse

from fpgaedu.shell import ExperimentationShell
from fpgaedu.shell.commands import ProgramCommand

class ShellSubcommand:

    name = 'shell'
    description = 'start a command line shell for interactive experimentation'

    def __init__(self):
        pass

    @staticmethod
    def execute(_):
        shell = ExperimentationShell()

        shell.commands[ProgramCommand.name] = ProgramCommand()

        shell.cmdloop()


    