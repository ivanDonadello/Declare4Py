"""Functions generating constraints as SIGNAL matches clauses according to
    Declare constraints.
"""


class Signal:
    def __init__(self) -> None:
        pass

    def init(self, element):
        """{element} is the first to occur"""
        return f"(^'{element}')"

    def end(self, element):
        """{element} is the last to occur"""
        return f"('{element}'$)"

    def precedence(self, predecessor, successor):
        """{successor} occurs only if it is preceded by {predecessor}. Activated by {successor}"""
        return f"(^ (NOT '{predecessor}' | ('{predecessor}' (NOT '{predecessor}')* '{successor}'))*$)"

    def alternate_precedence(self, predecessor, successor):
        """each time {successor} occurs, it is preceded by {predecessor} and no other
        {successor} can recur in between. Activated by {successor}"""
        return f"(^NOT('{successor}')*('{predecessor}' NOT('{successor}')*'{successor}'NOT('{successor}')*)*NOT('{successor}')*$)"

    def chain_precedence(self, predecessor, successor):
        """each time {successor} occurs, then {predecessor} occurs immediately beforehand.
        Activated by {successor}"""
        return f"(^NOT('{successor}')* ('{predecessor}' '{successor}'NOT('{successor}')*)*NOT('{successor}')*$)"

    def response(self, predecessor, successor):
        """if {predecessor} occurs, then {successor} occurs at some point after {predecessor}
        Activated by {predecessor}"""
        return f"(^NOT('{predecessor}')* ('{predecessor}' ANY*'{successor}')* NOT('{predecessor}')*$)"

    def alternate_response(self, predecessor, successor):
        """if {predecessor} occurs, then {successor} occurs at some point after
        {predecessor} and no other {predecessor} can recur in between. Activated by {predecessor}
        """
        return f"(^NOT('{predecessor}')*('{predecessor}'NOT('{predecessor}')*'{successor}'NOT('{predecessor}')*)*NOT('{predecessor}')*$)"

    def chain_response(self, predecessor, successor):
        """if {predecessor} occurs, then {successor} occurs immediately after {predecessor}
        and no other {predecessor} can recur in between. Activated by {predecessor}
        """
        return f"(^NOT('{predecessor}')* ('{predecessor}' '{successor}'NOT('{predecessor}')*)*NOT('{predecessor}')*$)"

    def succession(self, predecessor, successor):
        """{predecessor} occurs if and only if it is followed by {successor}.
        Activated by {predecessor} and {successor}"""
        return f"(^NOT('{predecessor}'|'{successor}')*('{predecessor}'~>'{successor}')*NOT('{predecessor}'|'{successor}')*$)"

    def alternate_succession(self, predecessor, successor):
        """{predecessor} occurs if and only if it is followed by {successor} and no other {predecessor}
        can recur in between. Activated by {predecessor} and {successor}"""
        return f"( ^ NOT('{predecessor}'|'{successor}')* ('{predecessor}'NOT('{predecessor}'|'{successor}')*'{successor}'NOT('{predecessor}'|'{successor}')*)*NOT('{predecessor}'|'{successor}')* $)"

    def chain_succession(self, predecessor, successor):
        """{predecessor} occurs if and only if {successor} occurs immediately after {predecessor}.
        Activated by {predecessor} and {successor}"""
        return f"(^NOT('{predecessor}'|'{successor}')* ('{predecessor}' '{successor}'NOT('{predecessor}'|'{successor}')*)*NOT('{predecessor}'|'{successor}')* $)"

    def choice(self, element_right, element_left):
        """{element_right} or {element_left} or both eventually occur
        in the same process instance (OR gateway). Activated by {element_right} and {element_left}
        """
        return f"(('{element_right}'|'{element_left}'))"

    def exclusive_choice(self, element_right, element_left):
        """{element_right} or {element_left} occurs, but never both in the same
        process instance (XOR gateway). Also called 'not co-existence'.
        Activated by {element_right} and {element_left}"""
        return f"(^(((NOT('{element_right}')*) ('{element_left}' NOT('{element_right}')*)*)|((NOT('{element_left}')*)('{element_right}' NOT('{element_left}')*)*))$)"

    def co_existence(self, element_right, element_left):
        """{element_right} and {element_left} occur in the same process instance (AND gateway).
        Activated by {element_right} and {element_left}"""
        return f"(^NOT('{element_right}'|'{element_left}')*(('{element_right}'ANY*'{element_left}'ANY*)|('{element_left}'ANY* '{element_right}' ANY*))* NOT('{element_right}'|'{element_left}')*$)"
