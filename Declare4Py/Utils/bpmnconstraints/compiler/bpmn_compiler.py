from itertools import combinations
from Declare4Py.Utils.bpmnconstraints.templates.declare_templates import Declare
from Declare4Py.Utils.bpmnconstraints.templates.matching_templates import Signal
from Declare4Py.Utils.bpmnconstraints.compiler.ltl.declare2ltl import Declare2ltl
from Declare4Py.Utils.bpmnconstraints.templates.LTLf_templates import LTLf
from Declare4Py.Utils.bpmnconstraints.utils.constants import *


class Compiler:
    def __init__(self, sequence, transitivity, skip_named_gateways) -> None:
        self.sequence = sequence
        self.transitivity = transitivity
        self.declare = Declare()
        self.signal = Signal()
        self.ltlf = LTLf()
        self.concurrent = True
        self.compiled_sequence = []
        self.cfo = None
        self.skip_named_gateways = skip_named_gateways

    def run(self):
        for cfo in self.sequence:
            self.cfo = cfo
            self.__compile()

        return self.compiled_sequence

    def __compile(self):
        if self.__cfo_is_start():
            self.__create_init_constraint()
        if self.__cfo_is_end():
            self.__create_end_constraint()

        if self.__is_activity():
            self.__create_succession_constraint()

        elif self.__is_gateway():
            if self.__cfo_is_splitting():
                self._create_gateway_constraints()
                self.__create_precedence_constraint()

            if self.__cfo_is_joining():
                if not self.__cfo_is_end():
                    self.__create_response_constraint()

    def _create_gateway_constraints(self):
        if self.__get_cfo_type() in XOR_GATEWAY:
            self.__create_exclusive_choice_constraint()

        if self.__get_cfo_type() == AND_GATEWAY:
            self.__create_parallel_gateway_constraint()
            self.concurrent = True

        if self.__get_cfo_type() == OR_GATEWAY:
            self.__create_inclusive_choice_constraint()

    def __create_succession_constraint(self):
        name = self.__get_cfo_name()
        successors = self.__get_cfo_successors()
        for successor in successors:
            if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                if self.__get_cfo_gateway_successors(successor):
                    successors.extend(self.__get_cfo_gateway_successors(successor))
        if self.transitivity:
            try:
                transitivity = self.__get_cfo_transitivity()
                transitivity = [x for x in transitivity if not self.__is_gateway(x)]
                successors.extend(transitivity)
            except Exception:
                pass

        for successor in successors:
            if self.__get_cfo_type(successor) in ALLOWED_END_EVENTS:
                continue
            successor_name = self.__get_cfo_name(successor)

            if successor_name in ALLOWED_GATEWAYS:
                continue

            if self.skip_named_gateways and successor["type"] in ALLOWED_GATEWAYS:
                continue

            if not self.__is_valid_name(successor_name) or not self.__is_valid_name(
                name
            ):
                continue

            if not successor.get("gateway successor"):
                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{name} leads to {successor_name}",
                        signal=self.signal.succession(name, successor_name),
                        declare=self.declare.succession(name, successor_name),
                        ltlf=self.ltlf.succession(name, successor_name)
                    )
                )

                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{name} and {successor_name}",
                        signal=self.signal.co_existence(name, successor_name),
                        declare=self.declare.co_existence(name, successor_name),
                        ltlf=self.ltlf.co_existence(name, successor_name)
                    )
                )

                if "is in gateway" not in self.cfo:
                    self.compiled_sequence.append(
                        self.__create_constraint_object(
                            description=f"{name} or {successor_name}",
                            signal=self.signal.choice(name, successor_name),
                            declare=self.declare.choice(name, successor_name),
                            ltlf=self.ltlf.choice(name, successor_name)
                        )
                    )

                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{name} leads to (with loops) {successor_name}",
                        signal=self.signal.alternate_succession(name, successor_name),
                        declare=self.declare.alternate_succession(name, successor_name),
                        ltlf=self.ltlf.alternate_succession(name, successor_name)
                    )
                )

    def __create_precedence_constraint(self):
        successors = self.__get_cfo_successors()
        predecessors = self.__get_cfo_predecessors()

        for successor in successors:
            if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                if self.__get_cfo_gateway_successors(successor):
                    successors.extend(self.__get_cfo_gateway_successors(successor))

        for successor in successors:
            successor_name = self.__get_cfo_name(successor)
            if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                continue

            if not self.__is_valid_name(successor_name):
                continue

            for predecessor in predecessors:
                predecessor_name = self.__get_cfo_name(predecessor)
                if self.__get_cfo_type(predecessor) in ALLOWED_GATEWAYS:
                    continue

                if not self.__is_valid_name(predecessor_name):
                    continue

                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{predecessor_name} precedes {successor_name}",
                        signal=self.signal.precedence(predecessor_name, successor_name),
                        declare=self.declare.precedence(
                            predecessor_name, successor_name
                        ),
                        ltlf=self.ltlf.precedence(predecessor_name, successor_name)
                    )
                )

                if self.concurrent:
                    self.compiled_sequence.append(
                        self.__create_constraint_object(
                            description=f"{predecessor_name} precedes {successor_name}",
                            signal=self.signal.alternate_precedence(
                                predecessor_name, successor_name
                            ),
                            declare=self.declare.alternate_precedence(
                                predecessor_name, successor_name
                            ),
                            ltlf=self.ltlf.alternate_precedence(
                                predecessor_name, successor_name
                            )
                        )
                    )

    def __is_valid_name(self, name):
        if name in ALLOWED_START_EVENTS:
            return False
        if name in ALLOWED_END_EVENTS:
            return False
        if name in ALLOWED_GATEWAYS:
            return False
        if name in GATEWAY_NAMES:
            return False
        return True

    def __cfo_is_start(self, cfo=None):
        if cfo:
            return cfo.get("is start")
        return self.cfo.get("is start")

    def __cfo_is_end(self, cfo=None):
        if cfo:
            return cfo.get("is end")
        return self.cfo.get("is end")

    def __cfo_is_splitting(self, cfo=None):
        if cfo:
            return cfo.get("splitting")
        return self.cfo.get("splitting")

    def __cfo_is_joining(self, cfo=None):
        if cfo:
            return cfo.get("joining")
        return self.cfo.get("joining")

    def __get_cfo_type(self, cfo=None):
        if cfo:
            return cfo.get("type")
        return self.cfo.get("type")

    def __get_cfo_successors(self, cfo=None):
        if cfo:
            return cfo.get("successor")
        return self.cfo.get("successor")

    def __get_cfo_predecessors(self, cfo=None):
        if cfo:
            return cfo.get("predecessor")
        return self.cfo.get("predecessor")

    def __get_cfo_transitivity(self, cfo=None):
        if cfo:
            return cfo.get("transitivity")
        return self.cfo.get("transitivity")

    def __get_cfo_gateway_successors(self, cfo=None):
        if cfo:
            return cfo.get("gateway successors")
        return self.cfo.get("gateway successors")

    def __create_response_constraint(self):
        successors = self.__get_cfo_successors()
        predecessors = self.__get_cfo_predecessors()

        for successor in successors:
            if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                if self.__get_cfo_gateway_successors(successor):
                    successors.extend(self.__get_cfo_gateway_successors(successor))

        for predecessor in predecessors:
            predecessor_name = self.__get_cfo_name(predecessor)
            if not self.__is_valid_name(predecessor_name):
                continue

            if self.__get_cfo_type(predecessor) in ALLOWED_GATEWAYS:
                continue

            for successor in successors:
                successor_name = self.__get_cfo_name(successor)
                if not self.__is_valid_name(successor_name):
                    continue

                if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                    continue

                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{predecessor_name} responds to {successor_name}",
                        signal=self.signal.response(predecessor_name, successor_name),
                        declare=self.declare.response(predecessor_name, successor_name),
                        ltlf=self.ltlf.response(predecessor_name, successor_name),
                    )
                )

                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{predecessor_name} responds to {successor_name}",
                        signal=self.signal.alternate_response(
                            predecessor_name, successor_name
                        ),
                        declare=self.declare.alternate_response(
                            predecessor_name, successor_name
                        ),
                        ltlf=self.ltlf.alternate_response(
                            predecessor_name, successor_name
                        ),
                    )
                )

    def __create_init_constraint(self):
        if self.__is_gateway():
            self.cfo.update({"discard": True})

        name = self.__get_cfo_name()
        self.compiled_sequence.append(
            self.__create_constraint_object(
                description=f"starts with {name}",
                signal=self.signal.init(name),
                declare=self.declare.init(name),
                ltlf=self.ltlf.init(name),
            )
        )

    def __create_end_constraint(self):
        name = self.__get_cfo_name()

        if not self.__is_valid_name(name):
            return

        self.compiled_sequence.append(
            self.__create_constraint_object(
                description=f"ends with {name}",
                signal=self.signal.end(name),
                declare=self.declare.end(name),
                ltlf=self.ltlf.end(name),
            )
        )

    def __create_exclusive_choice_constraint(self):
        successors = self.__get_cfo_successors()
        for successor in successors:
            if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                if self.__get_cfo_gateway_successors(successor):
                    successors.extend(self.__get_cfo_gateway_successors(successor))

        if successors:
            successors = [self.__get_cfo_name(successor) for successor in successors]
            for split in combinations(successors, 2):
                if not self.__is_valid_name(split[0]) or not self.__is_valid_name(
                    split[1]
                ):
                    continue
                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{split[0]} xor {split[1]}",
                        signal=self.signal.exclusive_choice(split[0], split[1]),
                        declare=self.declare.exclusive_choice(split[0], split[1]),
                        ltlf=self.ltlf.exclusive_choice(split[0], split[1]),
                    )
                )
                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{split[0]} or {split[1]}",
                        signal=self.signal.choice(split[0], split[1]),
                        declare=self.declare.choice(split[0], split[1]),
                        ltlf=self.ltlf.choice(split[0], split[1]),
                    )
                )

                predecessors = self.__get_cfo_predecessors()
                if predecessors:
                    for predecessor in predecessors:
                        predecessor_name = self.__get_cfo_name(predecessor)
                        for successor in successors:
                            if not self.__is_valid_name(
                                predecessor_name
                            ) or not self.__is_valid_name(successor):
                                continue
                            self.compiled_sequence.append(
                                self.__create_constraint_object(
                                    description=f"{predecessor_name} or {successor}",
                                    signal=self.signal.choice(
                                        predecessor_name, successor
                                    ),
                                    declare=self.declare.choice(
                                        predecessor_name, successor
                                    ),
                                    ltlf=self.ltlf.choice(
                                        predecessor_name, successor
                                    ),
                                )
                            )

    def __create_parallel_gateway_constraint(self):
        successors = self.__get_cfo_successors()
        for successor in successors:
            if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                if self.__get_cfo_gateway_successors(successor):
                    successors.extend(self.__get_cfo_gateway_successors(successor))

        if successors:
            successors = [self.__get_cfo_name(successor) for successor in successors]
            for split in combinations(successors, 2):
                if not self.__is_valid_name(split[0]) or not self.__is_valid_name(
                    split[1]
                ):
                    continue
                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{split[0]} and {split[1]}",
                        signal=self.signal.co_existence(split[0], split[1]),
                        declare=self.declare.co_existence(split[0], split[1]),
                        ltlf=self.ltlf.co_existence(split[0], split[1]),
                    )
                )

    def __create_inclusive_choice_constraint(self):
        successors = self.__get_cfo_successors()
        for successor in successors:
            if self.__get_cfo_type(successor) in ALLOWED_GATEWAYS:
                if self.__get_cfo_gateway_successors(successor):
                    successors.extend(self.__get_cfo_gateway_successors(successor))

        if successors:
            successors = [self.__get_cfo_name(successor) for successor in successors]
            for split in combinations(successors, 2):
                if not self.__is_valid_name(split[0]) or not self.__is_valid_name(
                    split[1]
                ):
                    continue
                self.compiled_sequence.append(
                    self.__create_constraint_object(
                        description=f"{split[0]} or {split[1]}",
                        signal=self.signal.choice(split[0], split[1]),
                        declare=self.declare.choice(split[0], split[1]),
                        ltlf=self.ltlf.choice(split[0], split[1]),
                    )
                )

            predecessors = self.__get_cfo_predecessors()
            if predecessors:
                for predecessor in predecessors:
                    predecessor_name = self.__get_cfo_name(predecessor)
                    for successor in successors:
                        if not self.__is_valid_name(
                            predecessor_name
                        ) or not self.__is_valid_name(successor):
                            continue
                        self.compiled_sequence.append(
                            self.__create_constraint_object(
                                description=f"{predecessor_name} or {successor}",
                                signal=self.signal.choice(predecessor_name, successor),
                                declare=self.declare.choice(
                                    predecessor_name, successor
                                ),
                                ltlf=self.ltlf.choice(
                                    predecessor_name, successor
                                ),
                            )
                        )

    def __get_cfo_name(self, cfo=None):
        if cfo:
            name = cfo.get("name")
        else:
            name = self.cfo.get("name")

        if not name or name == " ":
            if cfo:
                return self.__get_cfo_type(cfo)
            return self.__get_cfo_type()
        return name

    def __is_activity(self, cfo=None):
        if cfo:
            cfo_type = cfo.get("type")
        else:
            cfo_type = self.__get_cfo_type()
        if cfo_type:
            return cfo_type in ALLOWED_ACTIVITIES
        return False

    def __is_gateway(self, cfo=None):
        if cfo:
            cfo_type = cfo.get("type")
        else:
            cfo_type = self.__get_cfo_type()
        if cfo_type:
            return cfo_type in ALLOWED_GATEWAYS
        return False

    def __create_constraint_object(self, description, signal, declare, ltlf):
        return {
            "description": description,
            "SIGNAL": signal,
            "DECLARE": declare,
            "LTLf": ltlf,
        }
