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

from . import app_utils
from .__init__ import __appdescription__
from .__init__ import __appname__
from .__init__ import __status__
from .__init__ import __version__
from .python_utils import cli_utils
from .python_utils import exceptions


root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))

docopt_doc = """{appname} {version} ({status})

{appdescription}

Usage:
    app.py (-h | --help | --manual | --version)
    app.py del <patterns>...
               [-p <path> | --path=<path>]
               [-n | --negate]
               [-g | --glob]
    app.py edit (-l | --line-endings) <patterns>...
               [-p <path> | --path=<path>]
               [-n | --negate]
               [-g | --glob]
    app.py generate system_executable

Options:

-h, --help
    Show this screen.

--manual
    Show this application manual page.

--version
    Show application version.

-p <path>, --path=<path>
    Working directory. If not specified, the current working directory
    will be used.

-n, --negate
    Clean everything except specified patterns.

-g, --glob
    Clean with glob patterns.

-l, --line-endings
    Change line endings.

Important note:
    Each pattern in <patterns> should always be quoted.

""".format(appname=__appname__,
           appdescription=__appdescription__,
           version=__version__,
           status=__status__)


class CommandLineInterface(cli_utils.CommandLineInterfaceSuper):
    """Command line interface.

    It handles the arguments parsed by the docopt module.

    Attributes
    ----------
    a : dict
        Where docopt_args is stored.
    action : method
        Set the method that will be executed when calling CommandLineTool.run().
    cleaner : object
        See <class :any:`app_utils.FilesCleaner`>.
    glob_deletion : bool
        Whether or not to interpret the passed patters as glob patterns.
    """
    action = None

    def __init__(self, docopt_args):
        """
        Parameters
        ----------
        docopt_args : dict
            The dictionary of arguments as returned by docopt parser.

        Raises
        ------
        exceptions.MissingArgument
            Missing mandatory argument not passed.
        """
        self.a = docopt_args
        self._cli_header_blacklist = [self.a["--manual"]]

        super().__init__(__appname__)

        if not self.a["generate"] and not self.a["system_executable"] \
                and not self.a["--path"] and not self.a["--manual"]:
            msg = "Missing `--path` option.\n"
            msg += "Due to its nature, it is recommended to generate this application's\n"
            msg += "system executable and make use of it.\n"
            msg += "In doing so, the `--path` option will be automatically populated\n"
            msg += "with the current working directory.\n"
            msg += "Additional `--path` options can be passed."
            raise exceptions.MissingArgument(msg)

        if self.a["--manual"]:
            self.action = self.display_manual_page
        elif self.a["del"] or self.a["edit"]:
            self.glob_deletion = self.a["--glob"]
            self.cleaner = app_utils.FilesCleaner(path=self.a["--path"],
                                                  patterns=self.a["<patterns>"],
                                                  negate=self.a["--negate"],
                                                  logger=self.logger)
            if self.a["del"]:
                self.logger.info("**Deleting files...**")
                self.action = self.delete

            if self.a["edit"]:
                self.logger.info("**Cleaning files...**")
                self.action = self.edit
        elif self.a["generate"]:
            if self.a["system_executable"]:
                self.logger.info("**System executable generation...**")
                self.action = self.system_executable_generation

    def run(self):
        """Execute the assigned action stored in self.action if any.
        """
        if self.action is not None:
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
        """See :any:`cli_utils.CommandLineInterfaceSuper._system_executable_generation`.
        """
        self._system_executable_generation(
            exec_name="files-cleaner-cli",
            app_root_folder=root_folder,
            sys_exec_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "system_executable"),
            bash_completions_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "bash_completions.bash"),
            logger=self.logger
        )

    def display_manual_page(self):
        """See :any:`cli_utils.CommandLineInterfaceSuper._display_manual_page`.
        """
        self._display_manual_page(os.path.join(root_folder, "AppData", "data", "man", "app.py.1"))


def main():
    """Initialize command line interface.
    """
    cli_utils.run_cli(flag_file=".files-cleaner.flag",
                      docopt_doc=docopt_doc,
                      app_name=__appname__,
                      app_version=__version__,
                      app_status=__status__,
                      cli_class=CommandLineInterface)


if __name__ == "__main__":
    pass
