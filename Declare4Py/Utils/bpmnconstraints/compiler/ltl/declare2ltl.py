import logging
from pylogics.syntax.base import And, Implies, Not, Or
from pylogics.syntax.ltl import (
    Always,
    Eventually,
    Next,
    Until,
    PropositionalTrue,
    Atomic,
)
from pylogics.utils.to_string import to_string

# Declare Templates

EXISTENCE = "Existence"
ABSENCE = "Absence"
EXACTLY = "Exactly"

INIT = "Init"
END = "End"

CHOICE = "Choice"
EXCLUSIVE_CHOICE = "Exclusive Choice"
RESPONDED_EXISTENCE = "Responded Existence"
RESPONSE = "Response"
ALTERNATE_RESPONSE = "Alternate Response"
CHAIN_RESPONSE = "Chain Response"
PRECEDENCE = "Precedence"
ALTERNATE_PRECEDENCE = "Alternate Precedence"
CHAIN_PRECEDENCE = "Chain Precedence"

SUCCESSION = "Succession"
ALTERNATE_SUCCESSION = "Alternate Succession"
CHAIN_SUCCESSION = "Chain Succession"
CO_EXISTENCE = "Co-Existence"

NOT_CO_EXISTENCE = "Not Co-Existence"
NOT_RESPONDED_EXISTENCE = "Not Responded Existence"
NOT_RESPONSE = "Not Response"
NOT_CHAIN_RESPONSE = "Not Chain Response"
NOT_PRECEDENCE = "Not Precedence"
NOT_CHAIN_PRECEDENCE = "Not Chain Precedence"

NOT_SUCCESSION = "Not Succession"
NOT_ALTERNATE_SUCCESSION = "Not Alternate Succession"
NOT_CHAIN_SUCCESSION = "Not Chain Succession"


class Declare2ltl:
    def __init__(self) -> None:
        pass

    def to_ltl_str(self, constraint_str):
        try:
            formula = self.__to_ltl(constraint_str)
            if formula is None:
                return "Not translatable"
            return to_string(formula)
        except Exception:
            logging.error(constraint_str)
            return "Not translatable"

    def __to_ltl(self, constraint_str):
        n = 0
        templ_str = constraint_str.split("[")[0]
        if templ_str[-1].isdigit():
            n = int(templ_str[-1])
            templ_str = templ_str[:-1]
        activities = [
            act.strip() for act in constraint_str.split("[")[1].split("]")[0].split(",")
        ]
        activities = [act for act in activities if act != ""]
        if len(activities) == 0:
            return None
        activity_left = Atomic(activities[0].replace(" ", "_"))
        activity_right = None
        if len(activities) == 2:
            activity_right = Atomic(activities[1].replace(" ", "_"))
        if templ_str == ABSENCE:
            if n == 1:
                return Not(Eventually(activity_left))
            elif n == 2:
                return Not(
                    Eventually(And(activity_left, Next(Eventually(activity_left))))
                )
            elif n == 3:
                return Not(
                    Eventually(
                        And(
                            activity_left,
                            Next(
                                Eventually(
                                    And(activity_left, Next(Eventually(activity_left)))
                                )
                            ),
                        )
                    )
                )
            elif n == 4:
                return Not(
                    Eventually(
                        And(
                            activity_left,
                            Next(
                                Eventually(
                                    And(
                                        activity_left,
                                        Next(
                                            Eventually(
                                                And(
                                                    activity_left,
                                                    Next(Eventually(activity_left)),
                                                )
                                            )
                                        ),
                                    )
                                )
                            ),
                        )
                    )
                )
            else:
                raise ValueError("Unsupported n: " + str(n))

        elif templ_str == EXISTENCE:
            if n == 1:
                return Eventually(activity_left)
            elif n == 2:
                return Eventually(And(activity_left, Next(Eventually(activity_left))))
            elif n == 3:
                return Eventually(
                    And(
                        activity_left,
                        Next(
                            Eventually(
                                And(activity_left, Next(Eventually(activity_left)))
                            )
                        ),
                    )
                )
            else:
                raise ValueError("Unsupported n: " + str(n))

        elif templ_str == EXACTLY:
            if n == 1:
                return And(
                    self.__to_ltl(constraint_str.replace(EXACTLY, EXISTENCE)),
                    self.__to_ltl(constraint_str.replace(EXACTLY + "1", ABSENCE + "2")),
                )
            elif n == 2:
                return And(
                    self.__to_ltl(constraint_str.replace(EXACTLY, EXISTENCE)),
                    self.__to_ltl(constraint_str.replace(EXACTLY + "2", ABSENCE + "3")),
                )
            elif n == 3:
                return And(
                    self.__to_ltl(constraint_str.replace(EXACTLY, EXISTENCE)),
                    self.__to_ltl(constraint_str.replace(EXACTLY + "3", ABSENCE + "4")),
                )
            else:
                raise ValueError("Unsupported n: " + str(n))

        elif templ_str == INIT:
            return activity_left

        elif templ_str == END:
            return Eventually(And(activity_left, Next(Not(PropositionalTrue()))))

        elif templ_str == CHOICE:
            return Or(Eventually(activity_left), Eventually(activity_right))

        elif templ_str == EXCLUSIVE_CHOICE:
            return And(
                Or(Eventually(activity_left), Eventually(activity_right)),
                Not(And(Eventually(activity_left), Eventually(activity_right))),
            )

        elif templ_str == RESPONDED_EXISTENCE:
            return Implies(Eventually(activity_left), Eventually(activity_right))

        elif templ_str == RESPONSE:
            return Always(Implies(activity_left, Eventually(activity_right)))

        elif templ_str == ALTERNATE_RESPONSE:
            return Always(
                Implies(activity_left, Next(Until(Not(activity_left), activity_right)))
            )

        elif templ_str == CHAIN_RESPONSE:
            return Always(Implies(activity_left, Next(activity_right)))

        elif templ_str == PRECEDENCE:
            return Or(
                Until(Not(activity_right), activity_left), Always(Not(activity_right))
            )
        elif templ_str == ALTERNATE_PRECEDENCE:
            return And(
                Or(
                    Until(Not(activity_right), activity_left),
                    Always(Not(activity_right)),
                ),
                Always(
                    Implies(
                        activity_right,
                        Or(
                            Until(Not(activity_right), activity_left),
                            Always(Not(activity_right)),
                        ),
                    )
                ),
            )

        elif templ_str == CHAIN_PRECEDENCE:
            return Always(Implies(Next(activity_right), activity_left))

        elif templ_str == SUCCESSION:
            return And(
                self.__to_ltl(constraint_str.replace(SUCCESSION, RESPONSE)),
                self.__to_ltl(constraint_str.replace(SUCCESSION, PRECEDENCE)),
            )

        elif templ_str == ALTERNATE_SUCCESSION:
            return And(
                self.__to_ltl(
                    constraint_str.replace(ALTERNATE_SUCCESSION, ALTERNATE_RESPONSE)
                ),
                self.__to_ltl(
                    constraint_str.replace(ALTERNATE_SUCCESSION, ALTERNATE_PRECEDENCE)
                ),
            )

        elif templ_str == CHAIN_SUCCESSION:
            return And(
                self.__to_ltl(constraint_str.replace(CHAIN_SUCCESSION, CHAIN_RESPONSE)),
                self.__to_ltl(
                    constraint_str.replace(CHAIN_SUCCESSION, CHAIN_PRECEDENCE)
                ),
            )

        elif templ_str == CO_EXISTENCE:
            return And(
                Implies(Eventually(activity_left), Eventually(activity_right)),
                Implies(Eventually(activity_right), Eventually(activity_left)),
            )

        elif templ_str == NOT_RESPONDED_EXISTENCE:
            return Implies(Eventually(activity_left), Not(Eventually(activity_right)))
        elif templ_str == NOT_CHAIN_PRECEDENCE:
            return Always(Implies(Next(activity_right), Not(activity_left)))
        elif templ_str == NOT_PRECEDENCE:
            return Always(Implies(Eventually(activity_left), Not(activity_left)))
        elif templ_str == NOT_RESPONSE:
            return Always(Implies(activity_left, Not(Eventually(activity_right))))
        elif templ_str == NOT_CHAIN_RESPONSE:
            return Always(Implies(Next(activity_left), Not(activity_right)))
        elif templ_str == NOT_SUCCESSION:
            return And(
                self.__to_ltl(constraint_str.replace(NOT_SUCCESSION, NOT_RESPONSE)),
                self.__to_ltl(constraint_str.replace(NOT_SUCCESSION, NOT_PRECEDENCE)),
            )
        else:
            raise ValueError("Unknown template: " + constraint_str)
