"""Functions to generate Declare constraints.
"""


class Declare:
    def __init__(self) -> None:
        pass

    def init(self, element):
        """{element} is the first to occur"""
        return f"Init[{element}]"

    def end(self, element):
        """{element} is the last to occur"""
        return f"End[{element}]"

    def precedence(self, predecessor, successor):
        """{successor} occurs only if it is preceded by {predecessor}. Activated by {successor}"""
        return f"Precedence[{predecessor}, {successor}]"

    def alternate_precedence(self, predecessor, successor):
        """each time {successor} occurs, it is preceded by {predecessor} and no other {successor}
        can recur in between. Activated by {successor}"""
        return f"Alternate Precedence[{predecessor}, {successor}]"

    def chain_precedence(self, predecessor, successor):
        """
        each time {successor} occurs, then {predecessor} occurs immediately beforehand.
        Activated by {successor}
        """
        return f"Chain Precedence[{predecessor}, {successor}]"

    def response(self, predecessor, successor):
        """
        if {predecessor} occurs, then {successor} occurs at some point after {predecessor}.
        Activated by {predecessor}
        """
        return f"Response[{predecessor}, {successor}]"

    def alternate_response(self, predecessor, successor):
        """
        if {predecessor} occurs, then {successor} occurs at some point after {predecessor}
        and no other {predecessor} can recur in between. Activated by {predecessor}
        """
        return f"Alternate Response[{predecessor}, {successor}]"

    def chain_response(self, predecessor, successor):
        """
        if {predecessor} occurs, then {successor} occurs immediately after {predecessor}
        and no other {predecessor} can recur in between. Activated by {predecessor}
        """
        return f"Chain Response[{predecessor}, {successor}]"

    def succession(self, predecessor, successor):
        """
        {predecessor} occurs if and only if it is followed by {successor}.
        Activated by {predecessor} and {successor}
        """
        return f"Succession[{predecessor}, {successor}]"

    def alternate_succession(self, predecessor, successor):
        """{predecessor} occurs if and only if it is followed by {successor} and no other {predecessor}
        can recur in between. Activated by {predecessor} and {successor}"""
        return f"Alternate Succession[{predecessor}, {successor}]"

    def chain_succession(self, predecessor, successor):
        """{predecessor} occurs if and only if {successor} occurs immediately after {predecessor}.
        Activated by {predecessor} and {successor}"""
        return f"Chain Succession[{predecessor}, {successor}]"

    def choice(self, element_right, element_left):
        """
        {element_right} or {element_left} or both eventually occur
        in the same process instance (OR gateway).
        Activated by {element_right} and {element_left}
        """
        return f"Choice[{element_left}, {element_right}]"

    def exclusive_choice(self, element_right, element_left):
        """
        {element_right} or {element_left} occurs, but never both in the same process
        instance (XOR gateway). Also called 'not co-existence'.
        Activated by {element_right} and {element_left}
        """
        return f"Exclusive Choice[{element_left}, {element_right}]"

    def co_existence(self, element_right, element_left):
        """{element_right} and {element_left} occur in the same process instance (AND gateway).
        Activated by {element_right} and {element_left}"""
        return f"Co-Existence[{element_left}, {element_right}]"
