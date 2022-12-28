# pylint: disable=missing-docstring

from io import StringIO
from textwrap import dedent

from ningen import Writer


def assert_writes(writer: Writer, expected: str) -> None:
    actual_buffer = StringIO()
    writer.write(output=actual_buffer)
    actual = actual_buffer.getvalue()
    expected = dedent(expected)
    if expected[0] == "\n":
        expected = expected[1:]
    assert actual == expected


def test_scalar_variable():
    writer = Writer()
    writer.variable("variable_name", "variable value")
    assert_writes(
        writer,
        """
        variable_name = variable value
        """,
    )


def test_list_variable():
    writer = Writer()
    writer.variable("variable_name", ["variable", None, "value", None])
    assert_writes(
        writer,
        """
        variable_name = variable value
        """,
    )


def test_pool():
    writer = Writer()
    writer.pool("pool_name", 1)
    assert_writes(
        writer,
        """
        pool pool_name
          depth = 1
        """,
    )


def test_rule():
    writer = Writer()
    writer.rule("rule_name", ["some", "command line"])
    assert_writes(
        writer,
        """
        rule rule_name
          command = some command line
        """,
    )


def test_build():
    writer = Writer()
    writer.build("output_name", "rule_name", foo="bar")
    assert_writes(
        writer,
        """
        build output_name: rule_name
          foo = bar
        """,
    )


def test_build_repeated():
    writer = Writer()
    writer.build(["foo", "bar"], "first_rule_name")
    writer.build(["bar", "baz"], "second_rule_name")
    assert_writes(
        writer,
        """
        build foo bar: first_rule_name
        build bar baz: second_rule_name
        """,
    )


def test_build_override():
    writer = Writer()
    writer.build(["foo", "bar"], "first_rule_name")
    writer.build(["bar", "baz"], "second_rule_name", override=True)
    assert_writes(
        writer,
        """
        build foo: first_rule_name
        build bar baz: second_rule_name
        """,
    )


def test_build_replace():
    writer = Writer()
    writer.build(["foo"], "first_rule_name")
    writer.build(["foo"], "second_rule_name", override=True)
    assert_writes(
        writer,
        """
        build foo: second_rule_name
        """,
    )


def test_build_include():
    writer = Writer()
    writer.include("file_name")
    assert_writes(
        writer,
        """
        include file_name
        """,
    )


def test_build_subninja():
    writer = Writer()
    writer.subninja("file_name")
    assert_writes(
        writer,
        """
        subninja file_name
        """,
    )
