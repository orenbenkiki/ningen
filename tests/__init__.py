# pylint: disable=missing-docstring,invalid-name,consider-using-with,unspecified-encoding

import sys
from glob import glob
from os import chdir
from os import getcwd
from os import makedirs
from os import remove
from os.path import dirname
from os.path import expanduser
from os.path import isdir
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase


class TestWithFiles(TestCase):
    """
    Base class for running tests in a temporary directory.
    """

    def setUp(self) -> None:
        if sys.path[0] != getcwd():
            sys.path.insert(0, getcwd())
        self.previous_directory = getcwd()
        self.temporary_directory = mkdtemp()
        chdir(expanduser(self.temporary_directory))
        sys.path.insert(0, getcwd())

    def tearDown(self) -> None:
        chdir(self.previous_directory)
        rmtree(self.temporary_directory)

    @staticmethod
    def touch(path: str) -> None:
        directory = dirname(path)
        if directory:
            makedirs(directory, exist_ok=True)
        open(path, "w").close()

    @staticmethod
    def cleanUp() -> None:
        for path in glob("*"):
            if isdir(path):
                rmtree(path)
            else:
                remove(path)
