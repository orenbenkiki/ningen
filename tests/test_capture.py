# pylint: disable=missing-docstring

from typing import Dict
from typing import List
from typing import Optional
from unittest import TestCase

from ningen import capture2glob
from ningen import capture2re
from ningen import captures
from ningen import globs
from tests import TestWithFiles


class TestInvalidCapture(TestCase):
    def check_invalid(self, pattern: str, error: str) -> None:
        with self.assertRaisesRegex(ValueError, error):
            capture2re(pattern)
        with self.assertRaisesRegex(ValueError, error):
            capture2glob(pattern)

    def test_unclosed_one_star(self) -> None:
        self.check_invalid("{*foo", "missing }")

    def test_unclosed_two_stars(self) -> None:
        self.check_invalid("{**foo", "missing }")

    def test_invalid_first_name_character(self) -> None:
        self.check_invalid("{**1_}", "invalid first captured name character")

    def test_invalid_name_character(self) -> None:
        self.check_invalid("{**a-}", "invalid captured name character")

    def test_empty_name(self) -> None:
        self.check_invalid("{*}", "empty captured name")

    def test_empty_regexp(self) -> None:
        self.check_invalid("{*foo:}", "empty captured regexp")

    def test_unescaped_open(self) -> None:
        self.check_invalid("{", "unescaped { not followed by a \\*")

    def test_unescaped_close(self) -> None:
        self.check_invalid("}", "unescaped }")

    def test_unescaped_one(self) -> None:
        self.check_invalid("?", "unescaped \\? outside capture {\\*name:...\\}")

    def test_unescaped_any(self) -> None:
        self.check_invalid("*", "unescaped \\* outside capture {\\*name:...\\}")

    def test_unescaped_open_range(self) -> None:
        self.check_invalid("[", "unescaped \\[ outside capture {\\*name:...\\}")

    def test_unescaped_close_range(self) -> None:
        self.check_invalid("]", "unescaped \\] outside capture {\\*name:...\\}")


class TestValidCapture(TestCase):
    def check_pattern(self, *, pattern: str, glob: str, compiled: str, match: List[str], not_match: List[str]) -> None:
        self.assertEqual(capture2glob(pattern), glob)
        regexp = capture2re(pattern)
        self.assertEqual(str(regexp), f"re.compile('{compiled}')")
        for value in match:
            self.assertTrue(bool(regexp.fullmatch(value)), f"pattern: {pattern} value: {value}")
        for value in not_match:
            self.assertFalse(bool(regexp.fullmatch(value)), f"pattern: {pattern} value: {value}")

    def test_empty_pattern(self) -> None:
        self.check_pattern(pattern="", glob="", compiled="", match=[""], not_match=["a"])

    def test_literal_pattern(self) -> None:
        self.check_pattern(pattern="a", glob="a", compiled="a", match=["a"], not_match=["", "b", "/"])

    def test_escaped_pattern(self) -> None:
        self.check_pattern(pattern="{{}}", glob="{}", compiled="{}", match=["{}"], not_match=["{{}}"])

    def test_any_pattern(self) -> None:
        self.check_pattern(pattern="{*_:?}", glob="?", compiled="[^/]", match=["a", "b"], not_match=["", "/", "ab"])

    def test_many_pattern(self) -> None:
        self.check_pattern(
            pattern="{*_}.py", glob="*.py", compiled="[^/]*\\\\.py", match=[".py", "a.py"], not_match=["a_py", "/a.py"]
        )

    def test_deep_pattern(self) -> None:
        self.check_pattern(
            pattern="foo{**_}bar",
            glob="foo**bar",
            compiled="foo.*bar",
            match=["foobar", "foo/baz/bar"],
            not_match=["foo"],
        )

    def test_nest_pattern(self) -> None:
        self.check_pattern(
            pattern="foo/{**_}/bar",
            glob="foo/**/bar",
            compiled="foo/(?:.*/)?bar",
            match=["foo/bar", "foo/baz/bar"],
            not_match=["foo"],
        )
        self.check_pattern(
            pattern="foo/{*_:**}/bar",
            glob="foo/**/bar",
            compiled="foo/.*/bar",
            match=["foo/baz/bar"],
            not_match=["foo/bar"],
        )

    def test_nest_include_range(self) -> None:
        self.check_pattern(pattern="{*_:[a-z]}", glob="[a-z]", compiled="[a-z]", match=["c"], not_match=["C", "/"])

    def test_nest_exclude_range(self) -> None:
        self.check_pattern(pattern="{*_:[!a-z]}", glob="[!a-z]", compiled="[^/a-z]", match=["C"], not_match=["c", "/"])

        self.check_pattern(
            pattern="{*_:[^a-z]}", glob="[^a-z]", compiled="[\\\\^a-z]", match=["c", "^"], not_match=["C"]
        )

    def test_nest_include_backslash(self) -> None:
        self.check_pattern(pattern="{*_:[\\]}", glob="[\\]", compiled="[\\\\\\\\]", match=["\\"], not_match=["/"])

    def test_one_star(self) -> None:
        self.check_pattern(
            pattern="foo{*bar}baz",
            glob="foo*baz",
            compiled="foo(?P<bar>[^/]*)baz",
            match=["foobaz", "foobarbaz"],
            not_match=["", "foo/baz", "foobar/baz"],
        )

    def test_two_stars(self) -> None:
        self.check_pattern(
            pattern="foo{**bar}baz",
            glob="foo**baz",
            compiled="foo(?P<bar>.*)baz",
            match=["foobaz", "foo/baz", "foo/bar/baz"],
            not_match=[""],
        )

    def test_sub_dirs(self) -> None:
        self.check_pattern(
            pattern="foo/{**bar}/baz",
            glob="foo/**/baz",
            compiled="foo/(?:(?P<bar>.*)/)?baz",
            match=["foo/baz", "foo/bar/baz"],
            not_match=["", "foobaz", "foo/barbaz"],
        )

    def test_glob(self) -> None:
        self.check_pattern(
            pattern="foo{*bar:[0-9]}baz",
            glob="foo[0-9]baz",
            compiled="foo(?P<bar>[0-9])baz",
            match=["foo1baz"],
            not_match=["foo12baz", "fooQbaz"],
        )


class TestMatchCapture(TestCase):
    def check_pattern(self, *, pattern: str, captured: Dict[str, Optional[Dict[str, str]]]) -> None:
        for value, expected_captured in captured.items():
            actual_captured = captures(pattern, value, must_match=expected_captured is not None)
            if expected_captured is not None:
                expected_captured["path"] = value
                assert len(actual_captured) == 1
                self.assertEqual(actual_captured[0].__dict__, expected_captured)
            else:
                assert len(actual_captured) == 0

    def test_one_star(self) -> None:
        self.check_pattern(
            pattern="foo{*bar}baz", captured={"foo": None, "foobaz": dict(bar=""), "foobarbaz": dict(bar="bar")}
        )

    def test_two_stars(self) -> None:
        self.check_pattern(
            pattern="foo{**bar}baz",
            captured={"foobaz": dict(bar=""), "foo/baz": dict(bar="/"), "foo/bar/baz": dict(bar="/bar/")},
        )

    def test_sub_dirs(self) -> None:
        self.check_pattern(
            pattern="foo/{**bar}/baz",
            captured={"foobaz": None, "foo/baz": dict(bar=""), "foo/bar/baz": dict(bar="bar")},
        )

    def test_glob(self) -> None:
        self.check_pattern(
            pattern="foo{*bar:[0-9]}baz",
            captured={"fooQbaz": None, "foo1baz": dict(bar="1")},
        )


class TestGlobCapture(TestWithFiles):
    def check_pattern(self, *, pattern: str, captured: Dict[str, Optional[Dict[str, str]]]) -> None:
        for path, expected_captured in captured.items():
            self.touch(path)

            actual_captured = globs(pattern)
            if expected_captured is not None:
                assert len(actual_captured) == 1
                expected_captured["path"] = path
                self.assertEqual(actual_captured[0].__dict__, expected_captured)
            else:
                assert len(actual_captured) == 0

            self.cleanUp()

    def test_glob(self) -> None:
        self.check_pattern(
            pattern="foo{*bar:[0-9]}baz",
            captured={"fooQbaz": None, "foo1baz": dict(bar="1")},
        )
