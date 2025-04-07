from abc import ABC

from logaut import ltl2dfa

from Declare4Py.ProcessModels.AbstractModel import ProcessModel
from pylogics.parsers import parse_ltl
from Declare4Py.Utils.utils import Utils
from typing import List


class LTLModel(ProcessModel, ABC):

    def __init__(self, backend: str = "lydia"):
        super().__init__()
        self.formula: str = ""
        self.parsed_formula = None
        self.parameters = []
        self.backend = backend
        self.attribute_type = []

    def get_backend(self) -> str:
        """
        Returns the current backend used to translate an LTLf formula into a DFA.

        Returns:
            str: the current backend

        """
        return self.backend

    def to_lydia_backend(self) -> None:
        """
        Switch to lydia backend

        """
        self.backend = "lydia"

    def to_ltlf2dfa_backend(self) -> None:
        """
        Switch to ltlf2dfa backend

        """
        self.backend = "ltlf2dfa"

    def add_conjunction(self, new_formula: str) -> None:
        """
        This method puts in conjunction the LTLf formula of the class with the input LTLf formula

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) && ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_disjunction(self, new_formula: str) -> None:
        """
        This method puts in disjunction the LTLf formula of the class with the input LTLf formula

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) || ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_implication(self, new_formula: str) -> None:
        """
        This method add on implication between the LTLf formula of the class (left part) with the input LTLf formula
        (left part)

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) -> ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_equivalence(self, new_formula: str) -> None:
        """
        This method add o biimplication between the LTLf formula of the class (left part) with the input LTLf formula
        (left part)

        Args:
            new_formula: the LTLf
        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) <-> ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_negation(self) -> None:
        """
        This method negates the the LTLf formula of the class

        """
        self.formula = f"!({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_next(self) -> None:
        """
        This method adds the next operator in front of the LTLf formula of the class

        """
        self.formula = f"X[!]({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_eventually(self) -> None:
        """
        This method adds the eventually operator in front of the LTLf formula of the class

        """
        self.formula = f"F({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_always(self) -> None:
        """
        This method adds the always operator in front of the LTLf formula of the class

        """
        self.formula = f"G({self.formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def add_until(self, new_formula: str) -> None:
        """
        This method adds the until operator
        Args:
            new_formula:
                New formula to be added to the old formula through the until operator

        """
        new_formula = Utils.normalize_formula(new_formula)
        self.formula = f"({self.formula}) U ({new_formula})"
        self.parsed_formula = parse_ltl(self.formula)

    def check_satisfiability(self, minimize_automaton: bool = True) -> bool:
        """
        Checks satisfiability of the automata built on the parsed formula of the LTLModel object.
        Args:
            minimize_automaton:

        Returns:
            bool: If the automata is satisfied or not

        """
        if self.parsed_formula is None:
            raise RuntimeError("You must load the LTL model before checking the model.")
        if self.backend not in ["lydia", "ltlf2dfa"]:
            raise RuntimeError("Only lydia and ltlf2dfa are supported backends.")
        dfa = ltl2dfa(self.parsed_formula, backend=self.backend)
        if minimize_automaton:
            dfa = dfa.minimize()
        if len(dfa.accepting_states) > 0:
            return True
        else:
            return False
        
    def parse_from_diagram(self, line: str, activites):
        """
        Parses a xml file generated from a bpmn diagram. 
        args:
            line - A string containing the LTLf formula to parse
            activities - A list of activities generated from the DeclareModel

        Returns:
            Void
        """
        for word in activites:
            """ TODO: While this works currently, som modifications should be made to either parse_from_string or 
                the analyzer to make it applicable to all event logs """
            prefixed_word = 'con_' + word.replace(' ', '').lower()
            line = line.replace(word.replace(' ', '_'), prefixed_word)
            if line == word:
                line = word.replace(' ', '').lower()
                line = 'con_' + line

        self.parse_from_string(line)
        self.attribute_type = ["concept:name"]

        
    def parse_from_string(self, content: str, new_line_ctrl: str = "\n") -> None:
        """
        This function expects an LTL formula as a string.
        The pylogics library is used, reference to it in case of doubt.
        Refer to http://ltlf2dfa.diag.uniroma1.it/ltlf_syntax
        for allowed LTL symbols.
        We allow unary operators only if followed by parenthesis, e.g.: G(a), X(a), etc..

        Args:
            content: string containing the LTL formula to be passed

        Returns:
            Void

        """
        if type(content) is not str:
            raise RuntimeError("You must specify a string as input formula.")

        formula = Utils.normalize_formula(content)
        try:
            self.parsed_formula = parse_ltl(formula)
        except RuntimeError:
            raise RuntimeError(f"The inserted string: \"{formula}\" is not a valid LTL formula")

        self.formula = formula


class LTLTemplate:
    """
    Class that allows the user to create a LTLModel object containing one of the template formulae provided by this class.
    """

    def __init__(self, template_str: str):
        self.template_str: str = template_str
        self.parameters: [str] = []
        self.ltl_templates = {'eventually_a': self.eventually_a,
                              'eventually_a_and_eventually_b': self.eventually_a_and_eventually_b,
                              'eventually_a_then_b': self.eventually_a_then_b,
                              'eventually_a_or_b': self.eventually_a_or_b,
                              'eventually_a_next_b': self.eventually_a_next_b,
                              'eventually_a_then_b_then_c': self.eventually_a_then_b_then_c,
                              'eventually_a_next_b_next_c': self.eventually_a_next_b_next_c,
                              'next_a': self.next_a,
                              'p_does_a': self.p_does_a,
                              'a_is_done_by_p_and_q': self.a_is_done_by_p_and_q,
                              'p_does_a_and_b': self.p_does_a_and_b,
                              'p_does_a_and_then_b': self.p_does_a_and_then_b,
                              'p_does_a_and_eventually_b': self.p_does_a_and_eventually_b,
                              'p_does_a_a_not_b': self.p_does_a_a_not_b,
                              'a_done_by_p_p_not_q': self.a_done_by_p_p_not_q,
                              'is_first_state_a': self.is_first_state_a,
                              'is_second_state_a': self.is_second_state_a,
                              'is_third_state_a': self.is_third_state_a,
                              'is_last_state_a': self.is_last_state_a,
                              'is_second_last_state_a': self.is_second_last_state_a,
                              'is_third_last_state_a': self.is_third_last_state_a,
                              'last': self.last,
                              'second_last': self.second_last,
                              'third_last': self.third_last}

        self.tb_declare_templates = {'responded_existence': self.responded_existence,
                                     'response': self.response,
                                     'alternate_response': self.alternate_response,
                                     'chain_response': self.chain_response,
                                     'precedence': self.precedence,
                                     'alternate_precedence': self.alternate_precedence,
                                     'chain_precedence': self.chain_precedence,
                                     'not_responded_existence': self.not_responded_existence,
                                     'not_response': self.not_response,
                                     'not_precedence': self.not_precedence,
                                     'not_chain_response': self.not_chain_response,
                                     'not_chain_precedence': self.not_chain_precedence}

        self.templates = {**self.ltl_templates, **self.tb_declare_templates}

        if template_str in self.templates:
            self.template_str = template_str
        else:
            raise RuntimeError(f"{template_str} is a not a valid template. Check the tutorial here "
                               f"https://declare4py.readthedocs.io/en/latest/tutorials/2.Conformance_checking_LTL.html "
                               f"for a list of the valid templates")

    def get_ltl_templates(self) -> List[str]:
        """
        Retrieves the LTL template list

        Returns:
            A list containing all LTL templates.
        """
        return [template for template in self.ltl_templates]

    def get_tb_declare_templates(self) -> List[str]:
        """
        Retrieves the TBDeclare templates

        Returns:
            A list containing all TBDeclare templates.
        """
        return [template for template in self.tb_declare_templates]

    @staticmethod
    def add_conjunction(model: LTLModel, templates: List[str]) -> str:
        """
        Adds a list of selected template formulas to the formula of an already existing LTLModel object through means
        of conjunction.

        Args:
            model: Already existing LTLModel object
            templates: A list of templates to be added to the formula of the model

        Returns:
            The new formula
        """
        for templ in templates:
            model.add_conjunction(templ)
        return model.formula

    @staticmethod
    def next_a(activity: [str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: X[!](A). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "X[!](" + attr_type[0] + "_" + activity[0] + ")"
        return formula_str

    @staticmethod
    def eventually_a(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + ")"
        return formula_str

    @staticmethod
    def eventually_a_and_eventually_b(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A) && F(B). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + ") && " + "F(" + attr_type[0] + "_" + activity[1] + ")"
        return formula_str

    @staticmethod
    def eventually_a_then_b(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A && F(B)). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + " && F(" + attr_type[0] + "_" + activity[1] + "))"
        return formula_str

    @staticmethod
    def eventually_a_or_b(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A) || F(B). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + ") || F(" + attr_type[0] + "_" + activity[1] + ")"
        return formula_str

    @staticmethod
    def eventually_a_next_b(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A && X[!](B)). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + " && X[!](" + attr_type[0] + "_" + activity[1] + "))"
        return formula_str

    @staticmethod
    def eventually_a_then_b_then_c(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A && F(B && F(C))). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + " && F(" + attr_type[0] + "_" + activity[1] + " && F(" + \
                      attr_type[0] + "_" + activity[2] + ")))"
        return formula_str

    @staticmethod
    def eventually_a_next_b_next_c(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A && X[!](B && X[!](C))). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + " && X[!](" + attr_type[0] + "_" + activity[
            1] + " && X[!](" + attr_type[0] + "_" + activity[2] + ")))"
        return formula_str

    @staticmethod
    def is_first_state_a(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: A. This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = attr_type[0] + "_" + activity[0]
        return formula_str

    @staticmethod
    def is_second_state_a(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: X[!](A). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "X[!](" + attr_type[0] + "_" + activity[0] + ")"
        return formula_str

    @staticmethod
    def is_third_state_a(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: X[!](X[!](A)). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "X[!](X[!](" + attr_type[0] + "_" + activity[0] + "))"
        return formula_str

    @staticmethod
    def last(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: !(X[!](true)). It requires no attribute nor attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        formula_str = "!(X[!](true))"
        return formula_str

    @staticmethod
    def second_last(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: X[!](!(X[!](true))). It requires no attribute nor attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        formula_str = "X[!](!(X[!](true)))"
        return formula_str

    @staticmethod
    def third_last(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: X[!](X[!](!(X[!](true)))). It requires no attribute nor attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        formula_str = "X[!](X[!](!(X[!](true))))"
        return formula_str

    @staticmethod
    def is_last_state_a(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A && !(X[!](true))). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + " && " + LTLTemplate.last(activity, attr_type) + ")"
        return formula_str

    @staticmethod
    def is_second_last_state_a(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A && X[!](!(X[!](true)))). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + " && " + LTLTemplate.second_last(activity,
                                                                                                 attr_type) + ")"
        return formula_str

    @staticmethod
    def is_third_last_state_a(activity: List[str], attr_type: [str]) -> str:
        """
        Template of the LTL formula: F(A && X[!](X[!](!(X[!](true))))). This formula accepts only one attribute and one attribute type
        Args:
            activity: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activity = [Utils.parse_parenthesis(item) for item in activity]
        formula_str = "F(" + attr_type[0] + "_" + activity[0] + " && " + LTLTemplate.third_last(activity,
                                                                                                attr_type) + ")"
        return formula_str

    # Multiple attributes
    @staticmethod
    def p_does_a(activities: List[str], attr_type: List[str]) -> str:
        """
        The first attribute type (in attr_type) must be the type of the first attribute in the list activities.

        Args:
            activities: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string

        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities = [Utils.parse_parenthesis(item) for item in activities]
        formula_str = "F(" + attr_type[0] + "_" + activities[0] + " && " + attr_type[1] + "_" + activities[1] + ")"
        return formula_str

    @staticmethod
    def a_is_done_by_p_and_q(activities: List[str], attr_type: [str]) -> str:
        """
        The first attribute type (in attr_type) must be the type of the first attribute in the list activities.

        Args:
            activities: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string

        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities = [Utils.parse_parenthesis(item) for item in activities]
        formula_str = "(F(F(" + attr_type[0] + "_" + activities[0] + " && " + attr_type[1] + "_" + activities[
            2] + ")) && F(F(" + attr_type[0] + "_" + activities[1] + " && " + attr_type[1] + "_" + activities[2] + ")))"
        return formula_str

    @staticmethod
    def p_does_a_and_b(activities: List[str], attr_type: [str]) -> str:
        """
        The first attribute type (in attr_type) must be the type of the first attribute in the list activities.

        Args:
            activities: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string

        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities = [Utils.parse_parenthesis(item) for item in activities]
        formula_str = "(F(F(" + attr_type[0] + "_" + activities[0] + " &&  " + attr_type[1] + "_" + activities[
            1] + ")) && F(F(" + attr_type[0] + "_" + activities[0] + " &&  " + attr_type[1] + "_" + activities[
                          2] + ")))"
        return formula_str

    @staticmethod
    def p_does_a_and_then_b(activities: List[str], attr_type: [str]) -> str:
        """
        The first attribute type (in attr_type) must be the type of the first attribute in the list activities.

        Args:
            activities: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string

        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities = [Utils.parse_parenthesis(item) for item in activities]
        formula_str = "F((F(" + attr_type[0] + "_" + activities[0] + " && " + attr_type[1] + "_" + activities[
            1] + ") && X[!](F(" + attr_type[0] + "_" + activities[0] + " && " + attr_type[1] + "_" + activities[
                          2] + "))))"
        return formula_str

    @staticmethod
    def p_does_a_and_eventually_b(activities: List[str], attr_type: [str]) -> str:
        """
        The first attribute type (in attr_type) must be the type of the first attribute in the list activities.

        Args:
            activities: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string

        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities = [Utils.parse_parenthesis(item) for item in activities]
        formula_str = "F((F(" + attr_type[0] + "_" + activities[0] + " && " + attr_type[1] + "_" + activities[
            1] + ") && F(F(" + attr_type[0] + "_" + activities[0] + " && " + attr_type[1] + "_" + activities[2] + "))))"
        return formula_str

    @staticmethod
    def p_does_a_a_not_b(activities: List[str], attr_type: [str]) -> str:
        """
        The first attribute type (in attr_type) must be the type of the first attribute in the list activities.

        Args:
            activities: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string

        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities = [Utils.parse_parenthesis(item) for item in activities]
        formula_str = "F((" + attr_type[1] + "_" + activities[1] + " && " + "(!" + attr_type[1] + "_" + activities[
            2] + " && " + attr_type[0] + "_" + activities[0] + ")))"
        return formula_str

    @staticmethod
    def a_done_by_p_p_not_q(activities: List[str], attr_type: [str]) -> str:
        """
        The first attribute type (in attr_type) must be the type of the first attribute in the list activities.

        Args:
            activities: List of activities
            attr_type: List of attribute types

        Returns:
            The formula as a string

        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities = [Utils.parse_parenthesis(item) for item in activities]
        formula_str = "F((" + attr_type[0] + "_" + activities[0] + " && " + " (!" + attr_type[0] + "_" + activities[
            1] + " && " + attr_type[1] + "_" + activities[2] + ")))"
        return formula_str

    # Branched Declare Models
    @staticmethod
    def responded_existence(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type for both lists.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "F(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ") -> F(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ")"
        return formula

    @staticmethod
    def response(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G((" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ") -> F(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += "))"
        return formula

    @staticmethod
    def alternate_response(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G((" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ") -> X[!]((!(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ")U( " + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += "))))"
        return formula

    @staticmethod
    def chain_response(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G((" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += "  || " + attr_type[0] + "_" + activities_a[i]
        formula += ") -> X[!](" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += "))"
        return formula

    @staticmethod
    def precedence(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "((!(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += "))U(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ")) || G(!(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]

        formula += "))"
        return formula

    @staticmethod
    def alternate_precedence(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "((!(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += "))U(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ")) && G((" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ") -> X[!]((!(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += "))U(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ")) || G(!(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ")))"
        return formula

    @staticmethod
    def chain_precedence(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G(X[!](" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ") -> " + "(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += "))"
        return formula

    @staticmethod
    def not_responded_existence(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "F(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ") -> !(F(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += "))"
        return formula

    @staticmethod
    def not_response(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G((" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ") -> !(F(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ")))"
        return formula

    @staticmethod
    def not_precedence(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G(F(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ") ->!(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += "))"
        return formula

    @staticmethod
    def not_chain_response(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G((" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += ") -> X[!](!(" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ")))"
        return formula

    @staticmethod
    def not_chain_precedence(activities_a: List[str], activities_b: List[str], attr_type: [str]) -> str:
        """
        BDeclare template function. Takes two lists 'activation' and 'target' and a third list for the type of the attributes.
        This function accepts one attribute type.
        Args:
            activities_a: List of attributes, the 'source' list
            activities_b: List of attributes, the 'target' list
            attr_type: List of attribute types

        Returns:
            The formula as a string
        """
        attr_type = [Utils.encode_attribute_type(tipo) for tipo in attr_type]
        activities_a = [Utils.parse_parenthesis(item) for item in activities_a]
        activities_b = [Utils.parse_parenthesis(item) for item in activities_b]
        formula = "G( X[!](" + attr_type[0] + "_" + activities_b[0]
        for i in range(1, len(activities_b)):
            formula += " || " + attr_type[0] + "_" + activities_b[i]
        formula += ") -> !(" + attr_type[0] + "_" + activities_a[0]
        for i in range(1, len(activities_a)):
            formula += " || " + attr_type[0] + "_" + activities_a[i]
        formula += "))"
        return formula

    def fill_template(self, *attributes: List[str], attr_type: [str] = ["concept:name"]) -> LTLModel:
        """
        This function fills the template with the input lists of activities and returns an LTLModel object containing
        the filled LTLf formula of the template

        Args:
            attr_type: list of the attribute types to pass to the template functions, default contains only concept:name
            *attributes: list of attributes to pass to the template function

        Returns:
            LTLModel: LTLf Model of the filled formula of the template

        """
        if self.template_str is None:
            raise RuntimeError("Please first load a valid template")
        func = self.templates.get(self.template_str)
        filled_model = LTLModel()
        try:
            formula = func(*attributes, attr_type)
            for act in attributes:
                act = [item.lower() for item in act]
                act = [Utils.parse_parenthesis(item) for item in act]
                act = [Utils.parse_activity(item) for item in act]
                self.parameters += act
            filled_model.parse_from_string(formula)
            filled_model.parameters = self.parameters
            filled_model.attribute_type = attr_type
        except (TypeError, RuntimeError):
            raise TypeError("Mismatched number of parameters or type")
        return filled_model
