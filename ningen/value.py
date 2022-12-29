"""
Hold one or more values.
"""
from collections import abc
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

# pylint: disable=missing-docstring

__all__ = ["Value", "value_as_list", "values_dict"]


#: A value (or list of values) used in generating the ``ninja`` file.
#:
#: If this is a list, then ``None`` entries are silently ignored.
Value = Union[str, Sequence[Optional[str]]]


def value_as_list(value: Optional[Value]) -> List[str]:
    """
    Given a :py:class:`Value`, return a list of non-``None`` string values, for uniform processing.
    """
    if isinstance(value, str) or not isinstance(value, abc.Sequence):
        value = [value]
    values = [entry for entry in value if entry is not None]
    return values


def values_dict(values: Dict[str, Value]) -> Dict[str, List[str]]:
    """
    Given a dictionary of :py:class:`Value`, return a dictionary of lists of strings.
    """
    return {name: value_as_list(value) for name, value in values.items()}
