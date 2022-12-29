"""
Execute code with captured values.
"""
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

from .capture import Capture
from .capture import globs
from .value import Value
from .value import value_as_list
from .value import values_dict

__all__ = ["foreach", "expand"]


def foreach(  # pylint: disable=too-many-branches
    pattern: Optional[Value] = None, **kwargs: Value
) -> Iterator[Optional[Capture]]:
    """
    Execute code with captured values.

    The ``pattern`` should be a capture pattern (see :py:class:`ningen.capture.Capture` for details) or a list of such
    patterns (which presumably capture the same set of named parts of the file name).

    If additional named parameters (``kwargs``) are given, then the iterated capture is extended with each combination
    of these values.

    For example:

    .. code-block:: python

        for c in foreach("foo/{*name}.cc"):
            assert c.path == f"foo/{name}.cc"
            print(f"foo/{c.name}.cc exists on disk")

        for c in foreach("foo/{*name}.cc", mode=["debug", "release"], compiler=["gcc", "clang"]):
            print(f"compile foo/{c.name}.cc using the {c.compiler} compiler in {c.mode} mode")

        for c in foreach(mode=["debug", "release"], compiler=["gcc", "clang"]):
            print(f"final link step using the {c.compiler} compiler in {c.mode} mode")
    """
    if pattern is None:
        if not kwargs:
            return
        captured = [Capture()]  # type: ignore

    else:
        patterns = value_as_list(pattern)
        if not patterns:
            return

        captured = []
        for capture_pattern in patterns:
            captured += globs(capture_pattern)

        if not captured:
            return

    variables = values_dict(kwargs or {})
    for capture in captured:
        for name in variables:
            if name in capture.__dict__:
                raise ValueError(f"overriding the value of the captured: {name}")
        yield from _foreach(capture.__dict__, list(variables.items()))


def _foreach(data: Dict[str, str], items: List[Tuple[str, Value]]) -> Iterator[Capture]:
    if not items:
        yield Capture(**data)

    else:
        name, values = items[0]
        for value in value_as_list(values):
            data[name] = value
            yield from _foreach(data, items[1:])


def expand(template: Value, **kwargs: Value) -> List[str]:
    """
    Generate multiple formatted strings using all the combinations of the provided named values
    (``kwargs``).

    The ``template`` should be a normal Python format (using ``{name}``). If this is a list, then
    the result will contain the strings generated from all the non-``None`` templates in the list.

    Additional named parameters (``kwargs``) are expected. If one or more of these has a list
    of values, then a string will be generated for every combination of the values.

    For example:

    .. code-block:: python

        assert expand('src/{name}.cc', name='foo') == ['src/foo.cc']
        assert expand('src/{name}.cc', name=['foo', 'bar']) == ['src/foo.cc', 'src/bar.cc']
        assert expand('obj/{mode}/{name}.o', name=['foo', 'bar'], mode=['debug', 'release']) \
            == ['obj/debug/foo.o', 'obj/debug/bar.o', 'obj/release/foo.o', 'obj/release/bar.o']
    """
    results: List[str] = []
    templates = value_as_list(template)
    if templates and kwargs:
        _collect(templates, {}, list(values_dict(kwargs).items()), results)
    return results


def _collect(templates: List[str], data: Dict[str, str], items: List[Tuple[str, Value]], results: List[str]) -> None:
    if not items:
        for template in templates:
            results.append(template.format(**data))
        return

    name, values = items[0]
    for value in value_as_list(values):
        data[name] = value
        _collect(templates, data, items[1:], results)
