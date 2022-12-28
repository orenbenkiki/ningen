# pylint: disable=missing-docstring,undefined-variable

from unittest import TestCase

from ningen import expand
from ningen import foreach
from tests import TestWithFiles


class TestForeach(TestWithFiles):
    def test_foreach_nothing(self):
        for capture in foreach():
            print(capture)
            assert False

    def test_foreach_one(self):
        self.assertEqual([foo for _ in foreach(foo="bar")], ["bar"])  # noqa: F821

    def test_foreach_many(self):
        self.assertEqual([foo for _ in foreach(foo=["bar", "baz"])], ["bar", "baz"])  # noqa: F821

    def test_foreach_combination(self):
        self.assertEqual(
            [(foo, bar) for _ in foreach(foo=["a", "b"], bar=["1", "2"])],  # noqa: F821
            [("a", "1"), ("a", "2"), ("b", "1"), ("b", "2")],
        )

    def test_foreach_glob(self):
        self.touch("foo.cc")
        self.touch("bar.cc")
        self.assertEqual(sorted(list(foreach("{*name}.cc"))), sorted(["foo.cc", "bar.cc"]))
        self.assertEqual(sorted([name for _ in foreach("{*name}.cc")]), sorted(["foo", "bar"]))  # noqa: F821

    def test_foreach_glob_and_one(self):
        self.touch("foo.cc")
        self.touch("bar.cc")
        self.assertEqual(sorted(list(foreach("{*name}.cc", baz="baz"))), sorted(["foo.cc", "bar.cc"]))
        self.assertEqual(
            sorted([(name, baz) for _ in foreach("{*name}.cc", baz="baz")]),  # noqa: F821
            sorted([("foo", "baz"), ("bar", "baz")]),
        )

    def test_foreach_glob_and_many(self):
        self.touch("foo.cc")
        self.touch("bar.cc")
        self.assertEqual(sorted(list(foreach("{*name}.cc", baz=["1", "2"]))), sorted(["foo.cc", "bar.cc"] * 2))
        self.assertEqual(
            sorted([(name, baz) for _ in foreach("{*name}.cc", baz=["1", "2"])]),  # noqa: F821
            sorted([("foo", "1"), ("foo", "2"), ("bar", "1"), ("bar", "2")]),
        )

    def test_foreach_glob_and_override(self):
        self.touch("foo.cc")
        with self.assertRaisesRegex(ValueError, "overriding the value of the captured: name"):
            for _ in foreach("{*name}.cc", name="override"):
                pass


class TestExpand(TestCase):
    def test_expand_nothing(self):
        self.assertEqual(expand("foo"), [])

    def test_expand_one(self):
        self.assertEqual(expand("{foo}", foo="bar"), ["bar"])

    def test_expand_many(self):
        self.assertEqual(expand("{foo}", foo=["bar", "baz"]), ["bar", "baz"])

    def test_expand_combination(self):
        self.assertEqual(expand("{foo}.{bar}", foo=["a", "b"], bar=["1", "2"]), ["a.1", "a.2", "b.1", "b.2"])
