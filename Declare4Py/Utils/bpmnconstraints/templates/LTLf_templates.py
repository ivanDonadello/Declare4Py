from pylogics.syntax.base import And, Implies, Not, Or
from pylogics.syntax.ltl import (
    Always,
    Eventually,
    Next,
    PropositionalTrue,
    Atomic,
)
from pylogics.utils.to_string import to_string

class LTLf:
    def __init__(self) -> None:
        pass
            

    def init(self, element):
        """{element} is the first to occur"""
        return f"{element}"

    def end(self, element):
        """{element} is the last to occur"""
        formula = Eventually(And(Atomic(element.replace(" ", "_")), Next(Not(PropositionalTrue()))))
        return to_string(formula)

    def precedence(self, predecessor, successor, return_formula=False):
        pre_atom = Atomic(predecessor.replace(" ", "_"))
        suc_atom = Atomic(successor.replace(" ", "_"))
        # Replace Until with other logical constructs (if needed)
        formula = Or(Or(Eventually(suc_atom), And(Not(pre_atom), suc_atom)), Always(Not(pre_atom)))
        return formula if return_formula else to_string(formula)

    def alternate_precedence(self, predecessor, successor, return_formula=False):
        pre_atom = Atomic(predecessor.replace(" ", "_"))
        suc_atom = Atomic(successor.replace(" ", "_"))
        # Replace Until with other logical constructs
        formula = Always(Implies(suc_atom, And(Next(Not(suc_atom)), Or(Eventually(pre_atom), And(Not(suc_atom), pre_atom)))))
        return formula if return_formula else to_string(formula)

    def response(self, predecessor, successor, return_formula=False):
        pre_atom = Atomic(predecessor.replace(" ", "_"))
        suc_atom = Atomic(successor.replace(" ", "_"))
        formula = Always(Implies(pre_atom, Eventually(suc_atom)))
        return formula if return_formula else to_string(formula)

    def alternate_response(self, predecessor, successor, return_formula=False):
        pre_atom = Atomic(predecessor.replace(" ", "_"))
        suc_atom = Atomic(successor.replace(" ", "_"))
        # Replace Until with other logical constructs
        formula = Always(Implies(pre_atom, Next(Or(Eventually(suc_atom), And(Not(pre_atom), suc_atom)))))
        return formula if return_formula else to_string(formula)

    def chain_response(self, predecessor, successor, return_formula=False):
        pre_atom = Atomic(predecessor.replace(" ", "_"))
        suc_atom = Atomic(successor.replace(" ", "_"))
        formula = Always(Implies(pre_atom, Next(suc_atom)))
        return formula if return_formula else to_string(formula)

    def succession(self, predecessor, successor):
        precedence_formula = self.precedence(predecessor, successor, return_formula=True)
        response_formula = self.response(predecessor, successor, return_formula=True)
        combined_formula = And(response_formula, precedence_formula)
        return to_string(combined_formula)

    def alternate_succession(self, predecessor, successor):
        alternate_precedence_formula = self.alternate_precedence(predecessor, successor, return_formula=True)
        alternate_response_formula = self.alternate_response(predecessor, successor, return_formula=True)
        combined_formula = And(alternate_response_formula, alternate_precedence_formula)
        return to_string(combined_formula)

    def chain_succession(self, predecessor, successor):
        chain_response_formula = self.chain_response(predecessor, successor, return_formula=True)
        chain_precedence_formula = self.precedence(predecessor, successor, return_formula=True)
        combined_formula = And(chain_response_formula, chain_precedence_formula)
        return to_string(combined_formula)

    def choice(self, element_right, element_left):
        right_atom = Atomic(element_right.replace(" ", "_"))
        left_atom = Atomic(element_left.replace(" ", "_"))
        return to_string(Or(Eventually(right_atom), Eventually(left_atom)))

    def exclusive_choice(self, element_right, element_left):
        right_atom = Atomic(element_right.replace(" ", "_"))
        left_atom = Atomic(element_left.replace(" ", "_"))
        return to_string(And(Or(Eventually(right_atom), Eventually(left_atom)), Not(And(Eventually(right_atom), Eventually(left_atom)))))

    def co_existence(self, element_right, element_left):
        right_atom = Atomic(element_right.replace(" ", "_"))
        left_atom = Atomic(element_left.replace(" ", "_"))
        return to_string(And(Eventually(right_atom), Eventually(left_atom)))
