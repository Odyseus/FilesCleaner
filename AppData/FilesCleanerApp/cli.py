#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Main command line application.

Attributes
----------
docopt_doc : str
    Used to store/define the docstring that will be passed to docopt as the "doc" argument.
root_folder : str
    The main folder containing the application. All commands must be executed from this location
    without exceptions.
"""

import os
import sys

from . import app_utils
from .__init__ import __appname__, __appdescription__, __version__, __status__
from .python_utils import exceptions, log_system, shell_utils, file_utils
from .python_utils.docopt import docopt

if sys.version_info < (3, 5):
    raise exceptions.WrongPythonVersion()

root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))

# Store the "docopt" document in a variable to SHUT THE HELL UP Sphinx.
docopt_doc = """{__appname__} {__version__} {__status__}

{__appdescription__}

Usage:
    app.py del <patterns>...
               [-p <path> | --path=<path>]
               [-n | --negate]
               [-g | --glob]
    app.py edit (-l | --line-endings) <patterns>...
               [-p <path> | --path=<path>]
               [-n | --negate]
               [-g | --glob]
    app.py generate system_executable
    app.py (-h | --help | --version)

Options:

-h, --help
    Show this screen.

--version
    Show application version.

-p <path>, --path=<path>
    Working directory.

-n, --negate
    Clean everything except specified patterns.

-g, --glob
    Clean with glob patterns.

-l, --line-endings
    Change line endings.

Important note:
    <patterns> should always be quoted.

""".format(__appname__=__appname__,
           __appdescription__=__appdescription__,
           __version__=__version__,
           __status__=__status__)


class CommandLineTool():
    """Command line tool.

    It handles the arguments parsed by the docopt module.

    Attributes
    ----------
    action : method
        Set the method that will be executed when calling CommandLineTool.run().
    cleaner : object
        See <class :any:`app_utils.FilesCleaner`>.
    glob_deletion : bool
        Whether or not to interpret the passed patters as glob patterns.
    logger : object
        See <class :any:`LogSystem`>.
    """

    def __init__(self, args):
        """
        Parameters
        ----------
        args : dict
            The dictionary of arguments as returned by docopt parser.

        Raises
        ------
        exceptions.MissingArgument
            Missing mandatory argument not passed.
        """
        super(CommandLineTool, self).__init__()

        if not args["generate"] and not args["system_executable"] and not args["--path"]:
            msg = "Missing `--path` option.\n"
            msg += "Due to its nature, it is recommended to generate this application's\n"
            msg += "system executable and make use of it.\n"
            msg += "In doing so, the `--path` option will be automatically populated\n"
            msg += "with the current working directory.\n"
            msg += "Additional `--path` options can be passed."
            raise exceptions.MissingArgument(msg)

        self.action = None
        logs_storage_dir = "UserData/logs"
        log_file = log_system.get_log_file(storage_dir=logs_storage_dir,
                                           prefix="CLI")
        file_utils.remove_surplus_files(logs_storage_dir, "CLI*")
        self.logger = log_system.LogSystem(filename=log_file,
                                           verbose=True)

        self.logger.info(shell_utils.get_cli_header(__appname__), date=False)
        print("")

        if args["del"] or args["edit"]:
            self.glob_deletion = args["--glob"]
            self.cleaner = app_utils.FilesCleaner(path=args["--path"],
                                                  patterns=args["<patterns>"],
                                                  negate=args["--negate"],
                                                  logger=self.logger)

            if args["del"]:
                self.logger.info("Deleting files...")
                self.action = self.delete

            if args["edit"]:
                self.logger.info("Cleaning files...")
                self.action = self.edit

        if args["generate"]:
            if args["system_executable"]:
                self.logger.info("System executable generation...")
                self.action = self.system_executable_generation

    def run(self):
        """Execute the assigned action stored in self.action if any.
        """
        if self.action is not None:
            # pass
            self.action()

    def delete(self):
        """See :any:`app_utils.FilesCleaner._delete`
        """
        self.cleaner.run("glob_delete" if self.glob_deletion else "endswith_delete")

    def edit(self):
        """See :any:`app_utils.FilesCleaner._clean_endings`
        """
        self.cleaner.run("convert")

    def system_executable_generation(self):
        """See :any:`template_utils.system_executable_generation`
        """
        from .python_utils import template_utils

        template_utils.system_executable_generation(
            exec_name="files-cleaner-cli",
            app_root_folder=root_folder,
            sys_exec_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "system_executable"),
            bash_completions_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "bash_completions.bash"),
            logger=self.logger
        )


def main():
    """Initialize main command line interface.

    Raises
    ------
    exceptions.BadExecutionLocation
        Do not allow to run any command if the "flag" file isn't
        found where it should be. See :any:`exceptions.BadExecutionLocation`.
    """
    if not os.path.exists(".files-cleaner.flag"):
        raise exceptions.BadExecutionLocation()

    arguments = docopt(docopt_doc, version="%s %s %s" % (__appname__, __version__, __status__))
    cli = CommandLineTool(arguments)
    cli.run()


if __name__ == "__main__":
    pass
