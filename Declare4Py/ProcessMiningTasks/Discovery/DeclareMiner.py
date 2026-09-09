from __future__ import annotations

import os
from abc import ABC
from typing import Optional

from tqdm.auto import tqdm

from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessMiningTasks.AbstractDiscovery import AbstractDiscovery
from Declare4Py.ProcessModels.DeclareModel import DeclareModel, DeclareModelTemplate
from Declare4Py.Utils.Declare.Checkers import ConstraintChecker




"""
Provides basic discovery functionalities

Parameters
--------
    Discovery
        inherit class init

Attributes
--------
    super()
        inheriting from class Discovery
    output_path : str
        if specified, save the discovered constraints in a DECLARE model to the provided path.

"""


class DeclareMiner(AbstractDiscovery, ABC):

    def __init__(self, log: D4PyEventLog, consider_vacuity: bool, min_support: float, itemsets_support: float = 0.9,
                 max_declare_cardinality: int = 1, verbose: bool = True, output_path: str = None):
        """
        Args:
            log: the event log the constraints are discovered from.
            consider_vacuity: True means that vacuously satisfied traces are considered as satisfied, violated otherwise.
            min_support: the minimum fraction of traces a constraint must be satisfied in to be discovered.
            itemsets_support: the minimum support of the frequent item sets the candidate constraints are built from.
            max_declare_cardinality: the maximum cardinality checked for the templates supporting it.
            verbose: whether to report the amount of work and a progress bar while discovering.
            output_path: if specified, save the discovered DECLARE model to this path once the discovery completes.
        """
        super().__init__(log, DeclareModel(), min_support)
        self.consider_vacuity: bool = consider_vacuity
        self.itemsets_support: float = itemsets_support
        self.max_declare_cardinality: int = max_declare_cardinality
        self.verbose: bool = verbose
        self.output_path: Optional[str] = output_path

    def count_candidate_constraints(self, item_sets) -> int:
        """
        Counts the constraints 'run' will check for the given frequent item sets.

        Unary item sets yield one constraint per unary template (times 'max_declare_cardinality' for the templates
        supporting it), binary item sets one per binary non-shortcut template in both activity orders.

        Args:
            item_sets: the 'itemsets' column of the frequent item sets computed on the log.

        Returns:
            the number of constraints that will be checked against the whole log.
        """
        unary_per_item_set = sum(self.max_declare_cardinality if template.supports_cardinality else 1
                                 for template in DeclareModelTemplate.get_unary_templates())
        binary_per_item_set = 2 * len(DeclareModelTemplate.get_binary_not_shortcut_templates())

        total = 0
        for item_set in item_sets:
            if len(item_set) == 1:
                total += unary_per_item_set
            elif len(item_set) == 2:
                total += binary_per_item_set
        return total

    def run(self) -> DeclareModel:
        """
        Performs discovery of the supported DECLARE templates for the provided log by using the computed frequent item
        sets.

        The behaviour is configured through the constructor. When 'output_path' was given, the discovered model is
        also written to that path; when 'verbose' is set, the amount of work, a progress bar and the destination of
        the model are reported on standard output.

        Returns
        -------
        DeclareModel
            the model containing the constraints that reach 'min_support' over the log.
        """
        if self.event_log is None:
            raise RuntimeError("You must load a log before.")
        if self.max_declare_cardinality <= 0:
            raise RuntimeError("Cardinality must be greater than 0.")

        if self.output_path is not None:
            # Discovery can run for hours, so the destination is prepared now: failing at the end because the
            # directory does not exist would throw away the whole computation.
            output_path = os.path.abspath(self.output_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

        frequent_item_sets = self.event_log.compute_frequent_itemsets(min_support=self.itemsets_support,
                                                                      case_id_col=self.event_log.get_case_name(),
                                                                      categorical_attributes=[self.event_log.get_concept_name()],
                                                                      algorithm='fpgrowth', remove_column_prefix=True)

        tpm_activities = self.event_log.get_event_attribute_values(self.event_log.get_concept_name())
        if not isinstance(tpm_activities, list):
            self.process_model.activities = tpm_activities.keys()

        item_sets = list(frequent_item_sets['itemsets'])
        if self.verbose:
            # The runtime is driven by the number of candidate constraints, which grows quadratically with the number
            # of activities passing 'itemsets_support'. Reporting it up front makes an unfeasible run obvious
            # immediately instead of after hours of silence.
            print(f"Computing discovery ... {len(item_sets)} frequent item sets, "
                  f"{self.count_candidate_constraints(item_sets)} candidate constraints to check against "
                  f"{self.event_log.get_length()} traces")

        for item_set in tqdm(item_sets, desc="Discovering constraints", unit="itemset", disable=not self.verbose):
            length = len(item_set)
            if length == 1:
                for template in DeclareModelTemplate.get_unary_templates():
                    constraint = {"template": template, "activities": list(item_set), "condition": ("", "")}

                    if not template.supports_cardinality:
                        constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                       self.event_log,
                                                                                                       self.consider_vacuity,
                                                                                                       self.min_support)
                        # self.basic_discovery_results,= self.discover_constraint(self.event_log, constraint,
                        #                                                        self.consider_vacuity)
                        if constraint_satisfaction:
                            self.process_model.constraints.append(constraint.copy())
                    else:
                        for i in range(self.max_declare_cardinality):
                            constraint['n'] = i + 1
                            constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                           self.event_log,
                                                                                                           self.consider_vacuity,
                                                                                                           self.min_support)
                            # self.basic_discovery_results,= self.discover_constraint(self.event_log, constraint,
                            #                                                        self.consider_vacuity)
                            if constraint_satisfaction:
                                self.process_model.constraints.append(constraint.copy())

            elif length == 2:
                for template in DeclareModelTemplate.get_binary_not_shortcut_templates():
                    # constraint = {"template": templ, "activities": ', '.join(item_set), "condition": ("", "", "")}
                    constraint = {"template": template, "activities": list(item_set), "condition": ("", "", "")}
                    # self.basic_discovery_results,= self.discover_constraint(self.event_log, constraint,
                    #                                                        self.consider_vacuity)
                    constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                   self.event_log,
                                                                                                   self.consider_vacuity,
                                                                                                   self.min_support)
                    if constraint_satisfaction:
                        self.process_model.constraints.append(constraint.copy())
                    # constraint['activities'] = ', '.join(reversed(list(item_set)))

                    constraint['activities'] = list(reversed(list(item_set)))
                    # self.basic_discovery_results,= self.discover_constraint(self.event_log, constraint,
                    #                                                        self.consider_vacuity)
                    constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                   self.event_log,
                                                                                                   self.consider_vacuity,
                                                                                                   self.min_support)
                    if constraint_satisfaction:
                        self.process_model.constraints.append(constraint.copy())
        self.process_model.set_constraints()

        if self.output_path is not None:
            self.process_model.to_file(output_path)
        if self.verbose:
            message = f"Discovery completed: {len(self.process_model.serialized_constraints)} constraints discovered"
            if self.output_path is not None:
                message += f", DECLARE model saved to {output_path}"
            print(message)

        return self.process_model

    """
    def filter_discovery(self, min_support: float = 0, output_path: str = None) \
            -> Dict[str: Dict[Tuple[int, str]: CheckerResult]]:

        if self.event_log is None:
            raise RuntimeError("You must load a log before.")
        if self.basic_discovery_results is None:
            raise RuntimeError("You must run a Discovery task before.")
        if not 0 <= min_support <= 1:
            raise RuntimeError("Min. support must be in range [0, 1].")
        result = {}

        for key, val in self.basic_discovery_results.items():
            support = len(val) / len(self.event_log.log)
            if support >= min_support:
                result[key] = support

        if output_path is not None:
            with open(output_path, 'w') as f:
                f.write("activity " + "\nactivity ".join(self.event_log.get_log_alphabet_activities()) + "\n")
                f.write('\n'.join(result.keys()))
        return result

    def discover_constraint(self, log: D4PyEventLog, constraint: dict, consider_vacuity: bool):
        # Fake model composed by a single constraint
        model = DeclareModel()
        model.constraints.append(constraint)
        discovery_res: BasicDiscoveryResults = {}
        for i, trace in enumerate(log.log):
            trc_res = self.constraint_checker.check_trace_conformance(trace, model, consider_vacuity)
            if not trc_res:  # Occurring when constraint data conditions are formatted bad
                break
            constraint_str, checker_res = next(iter(trc_res.items()))  # trc_res will always have only one element
            # inside
            if checker_res.state == TraceState.SATISFIED:
                new_val = {(i, trace.attributes['concept:name']): checker_res}
                if constraint_str in discovery_res:
                    discovery_res[constraint_str],= new_val
                else:
                    discovery_res[constraint_str] = new_val
        return discovery_res
    """
