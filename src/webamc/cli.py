#!/usr/bin/env python3

import argparse
import random
import string

from webamc import db, config, VERSION, DATE
from webamc.all import *
from webamc.util import termout
from webamc.actions import (
    check, checklang, loadcsv, compile as comp, genexamples, gendoc, extract
)


def command_check(args: argparse.Namespace) -> None:
    check.action(args.input)


def command_checklang(_: argparse.Namespace) -> None:
    checklang.action()


def command_extract(args: argparse.Namespace) -> None:
    extract.action(args.input, args.output)


def command_gendoc(_: argparse.Namespace) -> None:
    if os.path.isdir(".git"):
        gendoc.action()
    else:
        termout.error("script must be executed from the git root directory")


def command_genexamples(args: argparse.Namespace) -> None:
    if os.path.isdir(args.output):
        genexamples.action(args.output)
    else:
        termout.error(f"directory not found: {args.output}")


def command_compile(args: argparse.Namespace) -> None:
    if os.path.isdir(args.input):
        if check.action(args.input):
            comp.action(args.input, args.prefix, args.threads)
    else:
        termout.error(f"directory not found: {args.input}")


def command_init(args: argparse.Namespace) -> None:
    def ask_confirmation() -> bool:
        word = "".join(
            list(map(lambda _: random.choice(string.ascii_letters), range(4)))
        )
        return word == input(f"confirm the operation by typing {word}\n")
    if args.force or ask_confirmation():
        db.op.init()
    else:
        print("deletion canceled")


def command_loadcsv(args: argparse.Namespace) -> None:
    delimiter: None | str = args.delimiter
    if delimiter is None:
        delimiter = ";"
    for i in args.input:
        loadcsv.action(i, delimiter)


def get_argparser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub_parsers = result.add_subparsers()

    result.add_argument(
        "-v", "--version", action='version',
        version=f"%(prog)s version {VERSION} ({DATE})",
        help="print version number and exit"
    )
    result.add_argument(
        "--config-file", type=str,
        help=(
            "specify the configuration file to be used "
            + f"(default is {config.DEFAULT_CONFIG_FILE})"
        )
    )

    # action check
    sub_parser = sub_parsers.add_parser(
        "check",
        help="check input directory"
    )
    sub_parser.add_argument(
        "input", type=str,
        help="input directory containing tex files"
    )
    sub_parser.set_defaults(command=command_check)

    # action compile
    sub_parser = sub_parsers.add_parser(
        "compile",
        help="compile tex files in input directory and produce a zip archive"
    )
    sub_parser.add_argument(
        "input", type=str,
        help="input directory containing tex files"
    )
    sub_parser.add_argument(
        "prefix", type=str,
        help="prefix of the archive produced"
    )
    sub_parser.add_argument(
        "--threads", type=int, default=4,
        help="number of threads/processes to use for compilation (default: 4)"
    )
    sub_parser.set_defaults(command=command_compile)

    # action genexamples
    sub_parser = sub_parsers.add_parser(
        "genexamples",
        help="generate csv example files"
    )
    sub_parser.add_argument(
        "output", type=str,
        help="ouput directory in which files will be generated"
    )
    sub_parser.set_defaults(command=command_genexamples)

    # action checklang
    sub_parser = sub_parsers.add_parser(
        "checklang",
        help="check language files for missing texts"
    )
    sub_parser.set_defaults(command=command_checklang)

    # action extract
    sub_parser = sub_parsers.add_parser(
        "extract",
        help="extract directory/files into separate question files"
    )
    sub_parser.add_argument(
        "input",
        help="input directory/file"
    )
    sub_parser.add_argument(
        "output",
        help="output directory"
    )
    sub_parser.set_defaults(command=command_extract)

    # action gendoc
    sub_parser = sub_parsers.add_parser(
        "gendoc",
        help="generate tex documentation files"
    )
    sub_parser.set_defaults(command=command_gendoc)

    # action init
    sub_parser = sub_parsers.add_parser(
        "init",
        help="initialise/reset the database"
    )
    sub_parser.add_argument(
        "--force", action="store_true",
        help="do not ask for confirmation"
    )
    sub_parser.set_defaults(command=command_init)

    # action loadcsv
    sub_parser = sub_parsers.add_parser(
        "loadcsv",
        help="load a csv to the database"
    )
    sub_parser.add_argument(
        "input", type=str, nargs="*",
        help="input csv file"
    )
    sub_parser.add_argument(
        "-d", "--delimiter", type=str,
        help="field delimiter (default is ';')"
    )
    sub_parser.set_defaults(command=command_loadcsv)

    return result


def main() -> None:
    arg_parser = get_argparser()
    arg_parsed = arg_parser.parse_args()
    if hasattr(arg_parsed, "command"):
        if arg_parsed.config_file is not None:
            config.DEFAULT_CONFIG_FILE = arg_parsed.config_file
        config.load()
        requiring_db = [
            command_init,
            command_loadcsv
        ]
        if arg_parsed.command in requiring_db:  # pylint: disable=W0143
            db.op.connect()
        arg_parsed.command(arg_parsed)
        if arg_parsed.command in requiring_db:  # pylint: disable=W0143
            db.op.close()
