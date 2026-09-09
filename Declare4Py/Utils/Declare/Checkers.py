from __future__ import annotations

import pdb
from abc import ABC
from datetime import timedelta
from functools import lru_cache
from math import ceil
from typing import List, Optional

from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessModels.DeclareModel import DeclareModel
from Declare4Py.ProcessModels.DeclareModel import DeclareModelConditionParserUtility, DeclareModelTemplate
from Declare4Py.Utils.Declare.TraceStates import TraceState
glob = {'__builtins__': None}


@lru_cache(maxsize=4096)
def _compile_cond(condition: str):
    """
    Compile a parsed activation/correlation/time condition into a code object.

    The checkers evaluate the same condition once per event of every trace. Passing the source string to eval() makes
    CPython re-parse and re-compile it on each call, which dominates the runtime of the discovery task. Code objects
    are accepted by eval() as-is, so caching them here keeps the semantics identical while paying the compilation
    cost only once per distinct condition.
    """
    return compile(condition, '<declare-condition>', 'eval')


class ConstraintChecker:

    def check_trace_conformance(self, trace: dict, decl_model: DeclareModel, consider_vacuity: bool = False,
                                concept_name: str = "concept:name") -> List[CheckerResult]:
        """
        Checks whether the constraints are fulfillment, violation, pendings, activations etc

        Parameters
        ----------
        :param bool consider_vacuity: True means that vacuously satisfied traces are considered as satisfied, violated otherwise
        :param d4pyEventLog trace: log
        :param DeclareModel decl_model: Process mining model
        Args:
            concept_name:
            concept_name:
        """

        # Set containing all constraints that raised SyntaxError in checker functions
        rules = {"vacuous_satisfaction": consider_vacuity}
        error_constraint_set = set()
        model: DeclareModel = decl_model
        trace_results = []
        for idx, constraint in enumerate(model.constraints):
            constraint_str = model.serialized_constraints[idx]
            rules["activation"] = constraint['condition'][0]
            if constraint['template'].supports_cardinality:
                rules["n"] = constraint['n']
            if constraint['template'].is_binary:
                rules["correlation"] = constraint['condition'][1]
            rules["time"] = constraint['condition'][-1]  # time condition is always at last position
            try:
                trace_results.append(TemplateConstraintChecker(trace, True, constraint['activities'], rules,
                                                               concept_name).get_template(constraint['template'])())
            except SyntaxError:
                # TODO: use python logger
                if constraint_str not in error_constraint_set:
                    error_constraint_set.add(constraint_str)
                    print('Condition not properly formatted for constraint "' + constraint_str + '".')
        return trace_results

    def constraint_checking_with_support(self, constraint: dict, event_log: D4PyEventLog, consider_vacuity: bool,
                                         min_support: float) -> bool:
        """
        Check wheter a constraint is satisfied in a log up to a given minimum support
        Args:
            consider_vacuity:
            event_log:
            min_support:
            constraint:

        Returns:

        """
        # Fake model composed by a single constraint
        tmp_model = DeclareModel()
        tmp_model.constraints.append(constraint)
        tmp_model.set_constraints()
        sat_ctr = 0

        for i, trace in enumerate(event_log.get_log()):
            trc_res = self.check_trace_conformance(trace, tmp_model, consider_vacuity, event_log.activity_key)
            if not trc_res:  # Occurring when constraint data conditions are formatted bad
                break
            # constraint_str, checker_res = next(iter(trc_res.items()))  # trc_res will always have only one element inside
            checker_res = trc_res[0]
            if checker_res.state == TraceState.SATISFIED:
                sat_ctr += 1
                # If the constraint is already above the minimum support, return it directly
                if sat_ctr / len(event_log.log) >= min_support:
                    return True #constraint_str
            # If there aren't enough more traces to reach the minimum support, return nothing
            if event_log.get_length() - (i + 1) < ceil(event_log.get_length() * min_support) - sat_ctr:
                return False # None
        return False # None

class TemplateConstraintChecker(ABC):

    def __init__(self, traces: dict, completed: bool, activities: List[str], rules: dict,
                 concept_name: str = "concept:name"):
        self.declare_parser_utility = DeclareModelConditionParserUtility()
        self.traces: dict = traces
        self.completed: bool = completed
        self.activities: List[str] = activities
        self.rules: dict = rules
        self.concept_name: str = concept_name

    def get_template(self, template: DeclareModelTemplate):
        """
        We have the classes with each template constraint checker and we invoke them dynamically
        and they check the result on given parameters
        Parameters
        ----------
        template: name of the declared model template
        traces
        completed
        activities: activities of declare model template which should be checked. Can be one or two activities
        rules: dict. conditions of template and 'n' for unary templates which represents 'n' times

        Returns
        -------

        """

        template_checker_name = f"mp{template.templ_str.replace(' ', '')}"
        try:
            return getattr(self, template_checker_name)
        except AttributeError:
            print(f"The checker function for template {template.templ_str} has not been implemented yet.")

    def mpChoice(self) -> CheckerResult:
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))
        a_or_b_occurs = False
        for A in self.traces:
            if A[self.concept_name] == self.activities[0] or A[self.concept_name] == self.activities[1]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    a_or_b_occurs = True
                    break
        state = None
        if not self.completed and not a_or_b_occurs:
            state = TraceState.POSSIBLY_VIOLATED
        elif self.completed and not a_or_b_occurs:
            state = TraceState.VIOLATED
        elif a_or_b_occurs:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    def mpExclusiveChoice(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))
        a_occurs = False
        b_occurs = False
        concept_name = self.concept_name
        activity_a, activity_b = self.activities[0], self.activities[1]
        first_event = self.traces[0] if len(self.traces) > 0 else None
        for A in self.traces:
            activity = A[concept_name]
            if (not a_occurs and activity == activity_a) or (not b_occurs and activity == activity_b):
                locl = {'A': A, 'T': first_event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    a_occurs = a_occurs or activity == activity_a
                    b_occurs = b_occurs or activity == activity_b
            if a_occurs and b_occurs:
                break
        state = None
        if not self.completed and (not a_occurs and not b_occurs):
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and (a_occurs ^ b_occurs):
            state = TraceState.POSSIBLY_SATISFIED
        elif (a_occurs and b_occurs) or (self.completed and (not a_occurs and not b_occurs)):
            state = TraceState.VIOLATED
        elif self.completed and (a_occurs ^ b_occurs):
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    """
        mp-existence constraint checker
        Description: The future constraining constraint existence(n, a) indicates that
        event a must occur at least n-times in the trace.
    """
    def mpExistence(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))
        num_activations = 0
        for A in self.traces:
            if A[self.concept_name] == self.activities[0]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    num_activations += 1
        n = self.rules["n"]
        state = None
        if not self.completed and num_activations < n:
            state = TraceState.POSSIBLY_VIOLATED
        elif self.completed and num_activations < n:
            state = TraceState.VIOLATED
        elif num_activations >= n:
            state = TraceState.SATISFIED
        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    """
        mp-absence constraint checker
        Description: The future constraining constraint absence(n + 1, a) indicates that
        event a may occur at most n − times in the trace.
    """
    def mpAbsence(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        num_activations = 0
        for A in self.traces:
            if A[self.concept_name] == self.activities[0]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    num_activations += 1

        n = self.rules["n"]
        state = None
        if not self.completed and num_activations < n:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_activations >= n:
            state = TraceState.VIOLATED
        elif self.completed and num_activations < n:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    """
        mp-init constraint checker
        Description: The future constraining constraint init(e) indicates
        that event e is the first event that occurs in the trace.
    """
    def mpInit(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))

        state = TraceState.VIOLATED
        if self.traces[0][self.concept_name] == self.activities[0]:
            locl = {'A': self.traces[0]}
            if eval(activation_rules, glob, locl):
                state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    """
        mp-init constraint checker
        Description: The future constraining constraint init(e) indicates
        that event e is the first event that occurs in the trace.
    """
    def mpEnd(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))

        state = TraceState.VIOLATED
        if self.traces[-1][self.concept_name] == self.activities[0]:
            locl = {'A': self.traces[-1]}
            if eval(activation_rules, glob, locl):
                state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    """
        mp-exactly constraint checker
    """
    def mpExactly(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))
        num_activations = 0
        for A in self.traces:
            if A[self.concept_name] == self.activities[0]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    num_activations += 1
        n = self.rules["n"]
        state = None
        if not self.completed and num_activations < n:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_activations == n:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_activations > n or (self.completed and num_activations < n):
            state = TraceState.VIOLATED
        elif self.completed and num_activations == n:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    # mp-responded-existence constraint checker
    # Description:
    # The future constraining and history-based constraint
    # respondedExistence(a, b) indicates that, if event a occurs in the trace
    # then event b occurs in the trace as well.
    # Event a activates the constraint.
    def mpRespondedExistence(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

        for event in self.traces:
            if not pendings:
                break

            if event[self.concept_name] == self.activities[1]:
                # Rebuilding the list is O(len(pendings)): removing by value would instead scan the list and compare
                # whole events, and pm4py's Event.__eq__ stringifies every attribute on each comparison.
                still_pending = []
                for A in pendings:
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        num_fulfillments += 1
                    else:
                        still_pending.append(A)
                pendings = still_pending

        if self.completed:
            num_violations = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif self.completed and num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings, num_activations=num_activations, state=state)

    def mpResponse(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

            if pendings and event[self.concept_name] == self.activities[1]:
                # See mpRespondedExistence: rebuilding keeps this linear in the number of pending activations.
                still_pending = []
                for A in pendings:
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        num_fulfillments += 1
                    else:
                        still_pending.append(A)
                pendings = still_pending

        if self.completed:
            num_violations = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_pendings > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_pendings == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif self.completed and num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings, num_activations=num_activations, state=state)

    # mp-alternate-response constraint checker
    # Description:
    # The future constraining constraint alternateResponse(a, b) indicates that
    # each time event a occurs in the trace then event b occurs afterwards
    # before event a recurs.
    # Event a activates the constraint.
    def mpAlternateResponse(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        pending = None
        num_activations = 0
        num_fulfillments = 0
        num_pendings = 0

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pending = event
                    num_activations += 1

            if event[self.concept_name] == self.activities[1] and pending is not None:
                locl = {'A': pending, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                    pending = None
                    num_fulfillments += 1

        if not self.completed and pending is not None:
            num_pendings = 1

        num_violations = num_activations - num_fulfillments - num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0 or (self.completed and num_pendings > 0):
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings, num_activations=num_activations, state=state)

    def mpChainResponse(self):
        """
        The future constraining constraint chain_response(a, b) indicates that, each time event a occurs in the trace,
        event b occurs immediately afterwards. Event a activates the constraint.
        Returns:

        """
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        num_activations = 0
        num_fulfillments = 0
        num_pendings = 0

        for index, event in enumerate(self.traces):

            if event[self.concept_name] == self.activities[0]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index < len(self.traces) - 1:
                        if self.traces[index + 1][self.concept_name] == self.activities[1]:
                            locl = {'A': event, 'T': self.traces[index + 1], 'timedelta': timedelta, 'abs': abs,
                                    'float': float}
                            if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                                num_fulfillments += 1
                    else:
                        if not self.completed:
                            num_pendings = 1

        num_violations = num_activations - num_fulfillments - num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0 or (self.completed and num_pendings > 0):
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings, num_activations=num_activations, state=state)

    def mpPrecedence(self):
        """
        The history-based constraint precedence(a,b) indicates that event b occurs only in the trace, if preceded by a.
        Event b activates the constraint.
        Returns:

        """
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        num_activations = 0
        num_fulfillments = 0
        Ts = []

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                Ts.append(event)

            if event[self.concept_name] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    for T in Ts:
                        locl = {'A': event, 'T': T, 'timedelta': timedelta, 'abs': abs, 'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_fulfillments += 1
                            break

        num_violations = num_activations - num_fulfillments
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)

    def mpAlternatePrecedence(self):
        """
        The history-based constraint alternatePrecedence(a, b) indicates that each time event b occurs in the trace
        it is preceded by event a and no other event b can recur in between. Event b activates the constraint.
        Returns:

        """
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        num_activations = 0
        num_fulfillments = 0
        Ts = []

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                Ts.append(event)

            if event[self.concept_name] == self.activities[1]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    num_activations += 1
                    for T in Ts:
                        locl = {'A': event, 'T': T, 'timedelta': timedelta, 'abs': abs, 'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_fulfillments += 1
                            break
                    Ts = []
        num_violations = num_activations - num_fulfillments
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None
        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED
        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)

    def mpChainPrecedence(self):
        """
        The history-based constraint chain_precedence(a, b) indicates that, each time event b occurs in the trace,
        event a occurs immediately beforehand. Event b activates the constraint.
        Returns:

        """
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        num_activations = 0
        num_fulfillments = 0

        for index, event in enumerate(self.traces):
            if event[self.concept_name] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index != 0 and self.traces[index - 1][self.concept_name] == self.activities[0]:
                        locl = {'A': event, 'T': self.traces[index - 1], 'timedelta': timedelta, 'abs': abs,
                                'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_fulfillments += 1

        num_violations = num_activations - num_fulfillments
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)

    def mpNotRespondedExistence(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

        for event in self.traces:
            if not pendings:
                break

            if event[self.concept_name] == self.activities[1]:
                # See mpRespondedExistence: rebuilding keeps this linear in the number of pending activations.
                still_pending = []
                for A in pendings:
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        num_violations += 1
                    else:
                        still_pending.append(A)
                pendings = still_pending

        if self.completed:
            num_fulfillments = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings, num_activations=num_activations, state=state)

    def mpNotResponse(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

            if pendings and event[self.concept_name] == self.activities[1]:
                # See mpRespondedExistence: rebuilding keeps this linear in the number of pending activations.
                still_pending = []
                for A in pendings:
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        num_violations += 1
                    else:
                        still_pending.append(A)
                pendings = still_pending

        if self.completed:
            num_fulfillments = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings, num_activations=num_activations, state=state)

    def mpNotPrecedence(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))

        num_activations = 0
        num_violations = 0
        Ts = []

        for event in self.traces:
            if event[self.concept_name] == self.activities[0]:
                Ts.append(event)

            if event[self.concept_name] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    for T in Ts:
                        locl = {'A': event, 'T': T, 'timedelta': timedelta, 'abs': abs, 'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_violations += 1
                            break

        num_fulfillments = num_activations - num_violations
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)

    def mpNotChainPrecedence(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))
        num_activations = 0
        num_violations = 0

        for index, event in enumerate(self.traces):

            if event[self.concept_name] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index != 0 and self.traces[index - 1][self.concept_name] == self.activities[0]:
                        locl = {'A': event, 'T': self.traces[index - 1], 'timedelta': timedelta, 'abs': abs,
                                'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_violations += 1

        num_fulfillments = num_activations - num_violations
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)

    def mpNotChainResponse(self):
        activation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["activation"]))
        correlation_rules = _compile_cond(self.declare_parser_utility.parse_data_cond(self.rules["correlation"]))
        time_rule = _compile_cond(self.declare_parser_utility.parse_time_cond(self.rules["time"]))
        num_activations = 0
        num_violations = 0
        num_pendings = 0

        for index, event in enumerate(self.traces):

            if event[self.concept_name] == self.activities[0]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index < len(self.traces) - 1:
                        if self.traces[index + 1][self.concept_name] == self.activities[1]:
                            locl = {'A': event, 'T': self.traces[index + 1], 'timedelta': timedelta, 'abs': abs,
                                    'float': float}
                            if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                                num_violations += 1
                    else:
                        if not self.completed:
                            num_pendings = 1

        num_fulfillments = num_activations - num_violations - num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings, num_activations=num_activations, state=state)


class CheckerResult:
    def __init__(self, num_fulfillments: Optional[int], num_violations: Optional[int], num_pendings: Optional[int],
                 num_activations: Optional[int], state: TraceState):
        self.num_fulfillments = num_fulfillments
        self.num_violations = num_violations
        self.num_pendings = num_pendings
        self.num_activations = num_activations
        self.state = state
