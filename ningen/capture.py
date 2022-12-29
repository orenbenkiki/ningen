"""
Capture parts from strings using a convenient glob-like syntax.
"""

import re
from dataclasses import dataclass
from glob import glob
from typing import Dict
from typing import List
from typing import Optional

from .value import Value
from .value import value_as_list

__all__ = ["captures", "globs", "Capture", "capture2glob", "capture2re"]


@dataclass
class Capture:
    """
    Capture the results of successfully matching a string (typically, a path name) with a capture
    pattern.

    A capture pattern is similar to a ``glob`` pattern. However, all wildcards must be specified
    inside ``{...}`` as follows:

    * You need to escape the ``{`` character as ``{{`` and the ``}`` character as ``}}``.

    * ``{*name}`` has the same effect as ``*``. The matching substring will be captured using the
       key ``name``. For example, ``foo.{*suffix}`` will capture the file suffix.

    * If ``name`` starts with ``_`` then the matching substring will be discarded instead of being
      captured. For example, if you don't want to capture the suffix, write ``foo.{*_}`` instead of
      ``foo.{*suffix}``.

    * If ``name`` is followed by ``:``, it must be followed by a glob pattern. That is, ``{*name}``
      is a shorthand for ``{*name:*}``. For example ``foo.{*suffix:[0-9]}`` will capture a single
      decimal digit suffix.

    * ``{**name}`` is shorthand for ``{*name:**}``. In this case you may not use ``:`` to specify
      a glob pattern. For example, ``foo/{**dir}/bar`` will capture all the (possibly empty) paths
      from ``foo`` to nested ``bar`` files.

    .. note::

        Use ``/{**name}/`` instead of ``/{*name:**}/`` as the shorthand is given special treatment
        allow for capturing an empty sub-directory (that is, match a single ``/``).

    The captured named values are available as members of the object, that is, write
    ``capture.foo`` to access the value of a captured ``{*foo}``.
    """

    def __init__(self, **kwargs: str) -> None:
        self.__dict__.update(kwargs)


def captures(pattern: str, values: Value, *, must_match: bool = False, name: str = "path") -> List[Capture]:
    """
    Given a capture ``pattern``, return all the :py:class:`Capture` results of applying it to each
    of the ``values``. If ``must_match``, all the values must match the pattern. Otherwise, only
    captures of matching values are returned.

    By default, the complete matched string is made available in a data member ``path`` (as this is typically used to
    parse disk file paths). You can override this by specifying a different ``name``.

    See :py:class:`Capture` for the description of the capture pattern.
    """
    results: List[Capture] = []
    regexp = capture2re(pattern)

    for value in value_as_list(values):
        parts = _capture_string_parts(regexp, value)
        if parts is not None:
            parts[name] = value
            results.append(Capture(**parts))
        elif must_match:
            raise ValueError(f"the value: {value} does not match the pattern: {pattern}")

    return results


def globs(pattern: str) -> List[Capture]:
    """
    Given a capture ``pattern``, return all the :py:class:`Capture` results of applying it to the
    results of a ``glob`` of the equivalent pattern.

    See :py:class:`Capture` for the description of the capture pattern.
    """
    return captures(pattern, glob(capture2glob(pattern)), must_match=True)


def _capture_string_parts(regexp: re.Pattern, string: str) -> Optional[Dict[str, str]]:
    match = re.fullmatch(regexp, string)
    if not match:
        return None

    values = match.groupdict()
    for name, value in values.items():
        if name and name[0] != "_":
            values[name] = str(value or "")
    return values


def capture2re(capture: str) -> re.Pattern:  # pylint: disable=too-many-statements
    """
    Convert a capture pattern to the equivalent ``re.Pattern``.
    """
    index = 0
    size = len(capture)
    results: List[str] = []

    def _is_next(expected: str) -> bool:
        nonlocal capture, index, size
        return index < size and capture[index] == expected

    def _invalid(reason: str = "") -> None:
        nonlocal capture, index
        raise ValueError(f'Invalid capture pattern:\n{capture}\n{index * " "}^ {reason}')

    def _expect_close() -> None:
        if not _is_next("}"):
            _invalid("missing }")
        nonlocal index
        index += 1

    def _parse_name(terminators: str) -> str:
        nonlocal capture, index, size
        start_index = index
        while index < size and capture[index] not in terminators:
            if index == start_index:
                if capture[index] != "_" and not capture[index].isalpha():
                    _invalid("invalid first captured name character")
            else:
                if capture[index] != "_" and not capture[index].isalnum():
                    _invalid("invalid captured name character")
            index += 1
        if index == start_index:
            _invalid("empty captured name")
        return capture[start_index:index]

    def _parse_regexp() -> str:
        nonlocal capture, index, size

        if not _is_next(":"):
            return ""
        index += 1

        start_index = index
        while index < size and capture[index] != "}":
            index += 1

        if index == start_index:
            _invalid("empty captured regexp")

        return _glob2re(capture[start_index:index])

    def _parse_two_stars() -> None:
        name = _parse_name("}")
        regexp = _parse_regexp() or ".*"
        _expect_close()

        nonlocal capture, index, size, results
        if results and results[-1] == "/" and index < size and capture[index] == "/":
            index += 1
            _append_regexp(name, regexp, "(?:", "/)?")
        else:
            _append_regexp(name, regexp)

    def _parse_one_star() -> None:
        name = _parse_name(":}")
        regexp = _parse_regexp() or "[^/]*"
        _expect_close()
        _append_regexp(name, regexp)

    def _append_regexp(name: str, regexp: str, prefix: str = "", suffix: str = "") -> None:
        nonlocal results
        results.append(prefix)
        if not name.startswith("_"):
            results.append("(?P<")
            results.append(name)
            results.append(">")
        results.append(regexp)
        if not name.startswith("_"):
            results.append(")")
        results.append(suffix)

    while index < size:
        char = capture[index]
        index += 1

        if char == "}":
            if _is_next("}"):
                results.append("}")
                index += 1
            else:
                _invalid("unescaped }")

        elif char == "{":
            if _is_next("{"):
                results.append("{")
                index += 1

            elif _is_next("*"):
                index += 1
                if _is_next("*"):
                    index += 1
                    _parse_two_stars()
                else:
                    _parse_one_star()

            else:
                _invalid("unescaped { not followed by a *")

        elif char in "*?[]":
            _invalid(f"unescaped {char} outside capture {{*name:...}}")

        else:
            results.append(re.escape(char))

    return re.compile("".join(results))


def _glob2re(glob: str) -> str:  # pylint: disable=too-many-branches,redefined-outer-name
    """
    Translate a ``glob`` pattern to the equivalent ``re.Pattern`` (as a string).

    This is subtly different from ``fnmatch.translate`` since we use it to match the result of a successful ``glob``
    rather than to actually perform the ``glob``.
    """
    index = 0
    size = len(glob)
    results: List[str] = []

    while index < size:
        char = glob[index]
        index += 1

        if char == "*":
            if index < size and glob[index] == "*":
                index += 1
                if results and results[-1] == "/" and index < size and glob[index] == "/":
                    results.append("(.*/)?")
                    index += 1
                else:
                    results.append(".*")
            else:
                results.append("[^/]*")

        elif char == "?":
            results.append("[^/]")

        elif char == "[":
            end_index = index
            while end_index < size and glob[end_index] != "]":
                end_index += 1

            if end_index >= size:
                results.append("\\[")

            else:
                characters = glob[index:end_index].replace("\\", "\\\\")
                index = end_index + 1

                results.append("[")

                if characters[0] == "!":
                    results.append("^/")
                    characters = characters[1:]
                elif characters[0] == "^":
                    results.append("\\")

                results.append(characters)
                results.append("]")

        elif char in "{}/":
            results.append(char)

        else:
            results.append(re.escape(char))

    return "".join(results)


def capture2glob(capture: str) -> str:  # pylint: disable=too-many-statements
    """
    Translate a capture pattern to the equivalent ``glob`` pattern.
    """
    index = 0
    size = len(capture)
    results: List[str] = []

    def _is_next(expected: str) -> bool:
        nonlocal capture, index, size
        return index < size and capture[index] == expected

    def _invalid(reason: str = "") -> None:
        nonlocal capture, index
        raise ValueError(f'Invalid capture pattern:\n{capture}\n{index * " "}^ {reason}')

    def _parse_glob(glob: str, terminators: str) -> None:  # pylint: disable=redefined-outer-name
        nonlocal capture, index, size
        start_index = index
        while index < size and capture[index] not in terminators:
            if index == start_index:
                if capture[index] != "_" and not capture[index].isalpha():
                    _invalid("invalid first captured name character")
            else:
                if capture[index] != "_" and not capture[index].isalnum():
                    _invalid("invalid captured name character")
            index += 1
        if index == start_index:
            _invalid("empty captured name")
        if index < size and capture[index] == ":":
            index += 1
            start_index = index
            while index < size and capture[index] != "}":
                index += 1
            if index == start_index:
                _invalid("empty captured regexp")
            glob = capture[start_index:index]
        if not _is_next("}"):
            _invalid("missing }")
        index += 1
        results.append(glob)

    while index < size:
        char = capture[index]
        index += 1

        if char == "}":
            if _is_next("}"):
                results.append("}")
                index += 1
            else:
                _invalid("unescaped }")

        elif char == "{":
            if _is_next("{"):
                results.append("{")
                index += 1

            elif _is_next("*"):
                index += 1
                if _is_next("*"):
                    index += 1
                    _parse_glob("**", "}")
                else:
                    _parse_glob("*", ":}")

            else:
                _invalid("unescaped { not followed by a *")

        elif char in "*?[]":
            _invalid(f"unescaped {char} outside capture {{*name:...}}")

        else:
            results.append(char)

    return "".join(results)
