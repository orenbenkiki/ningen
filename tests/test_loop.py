# pylint: disable=missing-docstring,invalid-name

from unittest import TestCase

from ningen import expand
from ningen import foreach
from tests import TestWithFiles


class TestForeach(TestWithFiles):
    @staticmethod
    def test_foreach_nothing():
        for capture in foreach():
            print(capture)
            assert False

    def test_foreach_one(self):
        self.assertEqual([c.foo for c in foreach(foo="bar")], ["bar"])

    def test_foreach_many(self):
        self.assertEqual([c.foo for c in foreach(foo=["bar", "baz"])], ["bar", "baz"])

    def test_foreach_combination(self):
        self.assertEqual(
            [(c.foo, c.bar) for c in foreach(foo=["a", "b"], bar=["1", "2"])],
            [("a", "1"), ("a", "2"), ("b", "1"), ("b", "2")],
        )

    def test_foreach_glob(self):
        self.touch("foo.cc")
        self.touch("bar.cc")
        self.assertEqual(
            sorted([(c.path, c.name) for c in foreach("{*name}.cc")]), sorted([("foo.cc", "foo"), ("bar.cc", "bar")])
        )

    def test_foreach_glob_and_one(self):
        self.touch("foo.cc")
        self.touch("bar.cc")
        self.assertEqual(
            sorted([(c.path, c.name, c.baz) for c in foreach("{*name}.cc", baz="baz")]),
            sorted([("foo.cc", "foo", "baz"), ("bar.cc", "bar", "baz")]),
        )

    def test_foreach_glob_and_many(self):
        self.touch("foo.cc")
        self.touch("bar.cc")
        self.assertEqual(
            sorted([(c.path, c.name, c.baz) for c in foreach("{*name}.cc", baz=["1", "2"])]),
            sorted([("foo.cc", "foo", "1"), ("foo.cc", "foo", "2"), ("bar.cc", "bar", "1"), ("bar.cc", "bar", "2")]),
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
