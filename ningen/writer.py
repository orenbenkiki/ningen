"""
Write ``ninja`` files.

This is similar to a ``ninja_syntax.Writer``, but allows for overriding the build statement for
targets, which makes it easier to use in a pattern-based generation policy.
"""
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from os import makedirs
from os.path import dirname
from typing import Dict
from typing import List
from typing import Optional
from typing import TextIO
from typing import Union

from ninja_syntax import Writer as RawWriter  # type: ignore

from .value import Value
from .value import value_as_list
from .value import values_dict

# pylint: disable=missing-docstring,fixme

__all__ = ["Writer"]


class Statement(ABC):  # pylint: disable=too-few-public-methods
    @abstractmethod
    def raw_write(self, raw_writer: RawWriter) -> None:
        ...


@dataclass
class Comment(Statement):
    text: str

    def raw_write(self, raw_writer: RawWriter) -> None:
        raw_writer.comment(**self.__dict__)


@dataclass
class Variable(Statement):
    key: str
    value: List[str]

    def raw_write(self, raw_writer: RawWriter) -> None:
        raw_writer.variable(**self.__dict__)


@dataclass
class Pool(Statement):
    name: str
    depth: int

    def raw_write(self, raw_writer: RawWriter) -> None:
        raw_writer.pool(**self.__dict__)


@dataclass  # pylint: disable=too-many-instance-attributes
class Rule(Statement):
    name: str
    command: List[str]
    description: List[str]
    pool: Optional[str]
    depfile: Optional[str]
    deps: Optional[str]
    generator: bool
    restat: bool
    rspfile: Optional[str]
    rspfile_content: List[str]

    def raw_write(self, raw_writer: RawWriter) -> None:
        raw_writer.rule(**self.__dict__)


@dataclass
class Build(Statement):
    outputs: List[str]
    rule: str
    inputs: List[str]
    implicit: List[str]
    order_only: List[str]
    implicit_outputs: List[str]
    variables: Optional[Dict[str, List[str]]]

    def raw_write(self, raw_writer: RawWriter) -> None:
        if self.outputs:
            raw_writer.build(**self.__dict__)


@dataclass
class Include(Statement):
    path: str

    def raw_write(self, raw_writer: RawWriter) -> None:
        raw_writer.include(**self.__dict__)


@dataclass
class SubNinja(Statement):
    path: str

    def raw_write(self, raw_writer: RawWriter) -> None:
        raw_writer.subninja(**self.__dict__)


# pylint: enable=missing-docstring


class Writer:
    """
    Write a ``ninja`` rules file using arbitrary logic (including querying the file system).
    """

    def __init__(self) -> None:
        self._statements: List[Statement] = []
        self._builds: Dict[str, int] = {}

    def write(self, *, output: Union[str, TextIO] = "build.ninja", width: int = 120) -> None:
        """
        Actually write the collected rules into the ``ninja`` rules file, using the specified line
        ``width``.

        If the ``output`` (default: ``"build.ninja"``) is a string, it is the name of a disk file to
        create and write into. Otherwise, it can be any Python ``TextIO`` object.

        .. note::

            Deferring writing the rules to the last moment allows us to provide additional
            functionality. Specifically it allows overriding "default" build statements with more
            specific ones.
        """
        if isinstance(output, str):
            directory = dirname(output)
            if directory:
                makedirs(directory, exist_ok=True)
            with open(output, "w", encoding="utf8") as file:
                self.write(output=file, width=width)

        else:
            raw_writer = RawWriter(output=output, width=width)
            for statement in self._statements:
                statement.raw_write(raw_writer)

    def comment(self, text: str) -> None:
        """
        Create a global ``ninja`` comment with some string ``text``.
        """
        self._statements.append(Comment(text=text))

    def variable(self, name: str, value: Value) -> None:
        """
        Create a global ``ninja`` variable with some string ``name`` and some
        :py:class:`ningen.value.Value` ``value``.
        """
        self._statements.append(Variable(key=name, value=value_as_list(value)))

    def pool(self, name: str, depth: int) -> None:
        """
        Create a ``ninja`` execution pool with some string ``name`` and some integer ``depth``.
        """
        self._statements.append(Pool(name=name, depth=depth))

    def rule(
        self,
        name: str,
        command: Value,
        *,
        description: Optional[Value] = None,
        depfile: Optional[str] = None,
        deps: Optional[str] = None,
        generator: bool = False,
        pool: Optional[str] = None,
        restat: bool = False,
        rspfile: Optional[str] = None,
        rspfile_content: Optional[Value] = None,
    ) -> None:
        """
        Create a ``ninja`` rule with some string ``name`` and some :py:class:`ningen.value.Value`
        ``command``.

        See the ``ninja`` documentation for the semantics of the arguments.
        """
        self._statements.append(
            Rule(
                name=name,
                command=value_as_list(command),
                description=value_as_list(description),
                depfile=depfile,
                deps=deps,
                generator=generator,
                pool=pool,
                restat=restat,
                rspfile=rspfile,
                rspfile_content=value_as_list(rspfile_content),
            )
        )

    def build(
        self,
        outputs: Value,
        rule: str,
        *,
        override: bool = False,
        inputs: Optional[Value] = None,
        implicit: Optional[Value] = None,
        order_only: Optional[Value] = None,
        implicit_outputs: Optional[Value] = None,
        # pool: Optional[str] = None, # TODO: Missing from ninja_syntax 1.7.2
        # msvc_deps_prefix: Optional[str] = None, # TODO: Missing from ninja_syntax 1.7.2
        # dyndep: Optional[str] = None, # TODO: Missing from ninja_syntax 1.7.2
        **variables: Value,
    ) -> None:
        """
        Create a ``ninja`` build statement for some :py:class:`ningen.value.Value` ``outputs`` using
        some named ``rule``.

        If ``override`` is ``True``, then this build statement will override any previous build
        statement(s) that were specified for any of the output(s), by simply removing them from the
        previous build statement(s) (if a build statement has no outputs left, it is simply
        ignored).

        This allows specifying generic default build statements for a set of targets, followed by
        specialized build statements for some special subset of the targets, without having to worry
        about "multiple rules may be used to generate" errors.

        .. note::

            Overriding only works if using the exact same output file name. That is, if you have one
            build statement for ``"./foo"`` and another for ``"foo"``, then the code will not
            understand that these refer to the same file and will pass both to the ``ninja`` build
            file, regardless of the value of ``override``.

        See the ``ninja`` documentation for the semantics of the arguments.
        """
        this_build_index = len(self._statements)
        this_build = Build(
            outputs=value_as_list(outputs),
            rule=rule,
            inputs=value_as_list(inputs),
            implicit=value_as_list(implicit),
            order_only=value_as_list(order_only),
            implicit_outputs=value_as_list(implicit_outputs),
            variables=values_dict(variables),
        )

        self._statements.append(this_build)

        for output in value_as_list(this_build.outputs):
            prev_build_index = self._builds.get(output)
            self._builds[output] = this_build_index

            if prev_build_index is not None and override:
                prev_build: Build = self._statements[prev_build_index]  # type: ignore
                prev_build.outputs.remove(output)

    def include(self, path: str) -> None:
        """
        Create a ``ninja`` ``include`` statement for some string ``path``.
        """
        self._statements.append(Include(path=path))

    def subninja(self, path: str) -> None:
        """
        Create a ``ninja`` ``subninja`` statement for some string ``path``.
        """
        self._statements.append(SubNinja(path=path))
