"""
The module provides several useful utility functions.

"""

__author__ = "Ilya Molodkin"
__date__ = "2023-04-22"
__version__ = "1.0"
__license__ = "MIT License"


from typing import Any, Union


def isNumerical(value: Any) -> bool:
    """Checks if the input value can be converted to a floating-point number
    :param value: The value to check
    :type value: Any

    :return: True if the value can be converted to a floating-point number, False otherwise
    :rtype: bool
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def notZero(initial_value: Union[float, int],
            value_if_zero: Union[float, int]) -> Union[float, int]:
    """
    Return `initial_value` if it is not zero, otherwise return `value_if_zero`
    :param initial_value:   A float or integer representing the initial value to be checked
    :param value_if_zero:   A float or integer representing the value to be returned if
                            `initial_value` is zero.

    :return:                A float or integer representing either `initial_value` or
                            `value_if_zero`, depending on the value of `initial_value`
    :rtype:                 Union[float, int]
    """
    return initial_value if initial_value else value_if_zero
