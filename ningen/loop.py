"""
Execute code with captured values.
"""
from inspect import stack
from typing import Any
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
) -> Iterator[Optional[str]]:
    """
    Execute code with captured values.

    The ``pattern`` should be a capture pattern (see :py:class:`Capture` for details) or a list of
    such patterns (which presumably capture the same set of named parts of the file name). In each
    invocation of the loop body, the captured named parts are made available (as global variables)
    to the code so they can be used directly. In addition, ``foreach`` will provide the full matched
    path as the loop variable.

    If additional named parameters (``kwargs``) are given, then they are also made available to the
    code. If one or more of these have a list of values, then the code will be invoked for each
    combination of the values. If no pattern is given, then the code will be invoked only for
    these combinations, and ``foreach`` will return ``None`` values.

    For example:

    .. code-block:: python

        for path in foreach("foo/{*name}.cc"):
            assert path == f"foo/{name}.cc"
            print(f"foo/{name}.cc exists on disk")

        for _ in foreach("foo/{*name}.cc", mode=["debug", "release"], compiler=["gcc", "clang"]):
            print(f"compile foo/{name}.cc using the {compiler} compiler in {mode} mode")

        for none in foreach(mode=["debug", "release"], compiler=["gcc", "clang"]):
            assert none is None
            print(f"final link step using the {compiler} compiler in {mode} mode")
    """
    if pattern is None:
        if not kwargs:
            return

        captured = [Capture(value=None, parts={})]  # type: ignore

    else:
        patterns = value_as_list(pattern)
        if not patterns:
            return

        captured = []
        for capture_pattern in patterns:
            captured += globs(capture_pattern)

        if not captured:
            return

    global_values = stack()[1][0].f_globals

    variables = values_dict(kwargs or {})
    for capture in captured:
        for name in variables:
            if name in capture.parts:
                raise ValueError(f"overriding the value of the captured: {name}")
        capture.parts.update(variables)  # type: ignore

        data: Dict[str, str] = {}
        for _ in _foreach(data, list(capture.parts.items())):

            old_values: Dict[str, Any] = {}
            created_values: List[str] = []

            for name, value in data.items():
                if value in global_values:
                    old_values[name] = global_values[name]
                else:
                    created_values.append(name)
                global_values[name] = value

            yield capture.value

            for name, value in old_values.items():
                global_values[name] = value

            for name in created_values:
                del global_values[name]


def _foreach(data: Dict[str, str], items: List[Tuple[str, Value]]) -> Iterator[None]:
    if not items:
        yield None

    else:
        name, values = items[0]
        for value in value_as_list(values):
            data[name] = value
            for _ in _foreach(data, items[1:]):
                yield None


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
