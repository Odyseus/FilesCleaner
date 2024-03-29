# -*- coding: utf-8 -*-
"""Application utilities.

Attributes
----------
root_folder : str
    The main folder containing the Knowledge Base. All commands must be executed
    from this location without exceptions.
"""

import os

from fnmatch import fnmatch
from shutil import rmtree

from .python_utils import prompts
from .python_utils.ansi_colors import Ansi


root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))


class FilesCleaner(object):
    """Recursively cleans patterns of files/directories.

    Attributes
    ----------
    actions : dict
        Possible actions to perform.
    cum_size : float
        Accumulated files size.
    logger : object
        See <class :any:`LogSystem`>.
    matchers : dict
        A dictionary of boolean function which takes a string and tries to match it against any
        one of the specified patterns, returning False otherwise.
    messages : dict
        Storage for messages used by the actions.
    targets : list
        The list of files/folders on which to perform actions.

    Note
    ----
    Based on: `a recipe from ActiveState <http://code.activestate.com/recipes/576643/>`__
    """

    def __init__(self, path, patterns, negate, logger):
        """Initialize.

        Parameters
        ----------
        path : str
            The path to work on.
        patterns : list
            The patterns to work with.
        negate : bool, optional
            If True, treat the patterns passed as non inclusive.
        logger : object
            See <class :any:`LogSystem`>.
        """
        self._path = path
        self._patterns = patterns
        self._negate = negate
        self.logger = logger

        self.matchers = {
            # A matcher is a boolean function which takes a string and tries
            # to match it against any one of the specified patterns,
            # returning False otherwise
            "endswith": lambda s: any(s.endswith(p) for p in patterns),
            "glob": lambda s: any(fnmatch(s, p) for p in patterns),
        }
        self.actions = {
            # action: (path_operating_func, matcher)
            "endswith_delete": (self._delete, "endswith"),
            "glob_delete": (self._delete, "glob"),
            "convert": (self._clean_endings, "endswith"),
        }
        self.messages = {
            # "function_name": ("Question?", "Info completed")
            "_delete": ("Delete files/folders", "Deleted"),
            "_clean_endings": ("Convert all Windows endings into Unix endings",
                               "Line endings cleaned for"),
        }
        self.targets = []
        self.cum_size = 0.0

    def __repr__(self):
        """__repr__ override.

        Returns
        -------
        str
            Printable representation of self.
        """
        return "<FilesCleaner: path:%s, negated:%s, patterns:%s>" % (
            self._path, self._negate, self._patterns)

    def _apply(self, func, confirm=False):
        """Applies a function to each target path

        Parameters
        ----------
        func : method
            The method used to handle a target depending on the action.
        confirm : bool, optional
            Ask for confirmation before performing an action.
        """
        i = 0
        errors = []
        question = "\n**{message} '{path}' \n{prompt}** "

        for target in self.targets:
            if confirm:
                answer = prompts.read_char(question.format(
                    message=self.messages[func.__name__][0],
                    path=target,
                    prompt=Ansi.LIGHT_YELLOW(
                        # Clean string:
                        # "(Yes/No/Abort)?"
                        "**(\033[4mY\033[24mes/\033[4mN\033[24mo/\033[4mA\033[24mbort)?**")
                ))

                if answer in {"y", "Y"}:  # i.e., Yes
                    try:
                        func(target)
                        i += 1
                    except Exception as err:
                        errors.append((func.__name__, target, str(err)))
                elif answer in {"a", "A"}:  # i.e., Abort
                    break
                else:  # i.e., No
                    continue
            else:
                try:
                    func(target)
                    i += 1
                except Exception as err:
                    errors.append(str(err))

        if i:
            self.logger.info("**%s %s items (%sK)**" % (
                self.messages[func.__name__][1], i, int(round(self.cum_size / 1024.0, 0))
            ), date=False)
        else:
            self.logger.info("**No action taken**", date=False)

        if len(errors) > 0:
            for err in errors:
                self.logger.error("**The following errors were found:**")
                self.logger.error(err, date=False)

    @staticmethod
    def _onerror(func, path, exc_info):
        """Error handler for :any:`shutil.rmtree`.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.

        Parameters
        ----------
        func : method
            The function that triggered the error.
        path : str
            Argument to be used by func.
        exc_info : tuple
            A tuple returned by sys.exc_info().

        Example
        -------
        .. code::

            shutil.rmtree(path, onerror=onerror)

        Original code by Michael Foord.
        Bug fix suggested by Kun Zhang.
        """
        import stat

        if not os.access(path, os.W_OK):
            # Is the error an access error ?
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    def run(self, action):
        """Finds pattern and approves action on results.

        Parameters
        ----------
        action : str
            The action to perform.
        """
        self.logger.info("**Working inside directory:**\n%s" % self._path, date=False)
        func, matcher = self.actions[action]

        def show(path):
            """Function used to filter paths.

            Parameters
            ----------
            path : str
                The path to apply the filter on.

            Returns
            -------
            bool
                If the path should be shown of not.
            """
            if self._negate:
                return path if not self.matchers[matcher](path) else None
            else:
                return path if self.matchers[matcher](path) else None

        results = self._walk(self._path, show)

        if results:
            question = "**{results} item(s) found. {message} {prompt}** "

            answer = prompts.read_char(question.format(
                results=len(results),
                message=self.messages[func.__name__][0],
                prompt=Ansi.LIGHT_YELLOW(
                    # Clean string:
                    # "(Yes/No/Confirm)?"
                    "**(\033[4mY\033[24mes/\033[4mN\033[24mo/\033[4mC\033[24monfirm)?**")
            ))
            self.targets = results

            if answer in {"y", "Y"}:
                self._apply(func)
            elif answer in {"c", "C"}:
                self._apply(func, confirm=True)
            else:
                self.logger.warning("**Action cancelled.**", date=False)
        else:
            self.logger.info("**No results.**", date=False)

    def _walk(self, path, func):
        """Walk path recursively collecting results of function application.

        Parameters
        ----------
        path : str
            The path to *walk*.
        func : method
            The function used to filter the *walked* path.

        Returns
        -------
        list
            The list of files/folders paths.
        """
        results = []

        def visit(root, target, prefix):
            """Visit path.

            Parameters
            ----------
            root : str
                The root folder to *walk*.
            target : str
                The list of files/folders relative to the root folder.
            prefix : str
                Prefix used to differentiate files form folders.
            """
            for t in target:
                item = os.path.join(root, t)
                obj = func(item)

                if obj:
                    results.append(obj)
                    self.cum_size += os.path.getsize(obj)

                    self.logger.info("**%s** %s" %
                                     (prefix, os.path.relpath(obj, self._path)), date=False)

        for root, dirs, files in os.walk(path):
            visit(root, dirs, "+-->")
            visit(root, files, "|-->")

        return results

    def _delete(self, path):
        """Delete path.

        Parameters
        ----------
        path : str
            The path to the file to delete.
        """
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            rmtree(path, onerror=self._onerror)

    def _clean_endings(self, path):
        """Convert Windows line endings to Unix line endings.

        Parameters
        ----------
        path : str
            The path to the file to "clean up".
        """
        with open(path, "r", encoding="cp1252") as old:
            lines = old.readlines()

        string = "".join(l.rstrip() + "\n" for l in lines)

        with open(path, "w", encoding="UTF-8") as new:
            new.write(string)


if __name__ == "__main__":
    pass
