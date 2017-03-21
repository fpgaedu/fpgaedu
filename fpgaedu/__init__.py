import sys
import argparse

from fpgaedu.subcommands import ShellSubcommand

SUBCOMMANDS = {
    ShellSubcommand.name: ShellSubcommand
}

def create_main_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand")
    for cmd_name, cmd_class in SUBCOMMANDS.items():
        subparsers.add_parser(cmd_name, description=cmd_class.description)
    return parser

def main(argv=None):

    if argv is None:
        argv = sys.argv

    parser = create_main_parser()
    options = parser.parse_args(argv[1:])

    if options.subcommand in SUBCOMMANDS:
        SUBCOMMANDS[options.subcommand].execute(options)
    else:
        parser.print_help()
