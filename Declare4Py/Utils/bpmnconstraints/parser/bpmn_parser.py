import logging
from pathlib import Path
from json import load, JSONDecodeError
from xml.etree import ElementTree
from Declare4Py.Utils.bpmnconstraints.utils.constants import *
from Declare4Py.Utils.bpmnconstraints.utils.sanitizer import Sanitizer
from Declare4Py.Utils.bpmnconstraints.parser.json_model import JsonModel
from Declare4Py.Utils.bpmnconstraints.parser.xml_model import XmlModel


class Parser:
    def __init__(self, bpmn, is_file, transitivity) -> None:
        self.transitivity = transitivity
        self.bpmn_model = self.__create_model(bpmn, is_file)
        self.bpmn_diagram = self.bpmn_model
        self.sequence = []
        self.is_json = is_file and Path(bpmn).suffix == ".json"
        self.sanitizer = Sanitizer()
        self.model = None

    def __flatten_model(self):
        self.bpmn_model[CHILD_SHAPES] = self.__flatten(self.bpmn_model)

    def __create_model(self, bpmn, is_file):
        if is_file:
            try:
                file_extension = Path(bpmn).suffix
                if not file_extension or file_extension not in [".json", ".xml"]:
                    return None
                elif file_extension == ".xml":
                    return ElementTree.parse(bpmn).getroot()
                elif file_extension == ".json":
                    with open(bpmn, "r", encoding="utf-8") as file:
                        return load(file)
            except JSONDecodeError:
                raise Exception("Something wrong with format of JSON file.")
            except OSError:
                raise Exception("Something went wrong reading the file.")
        else:
            return bpmn

    def __flatten(self, model):
        elements = []
        for elem in model[CHILD_SHAPES]:
            if self.model.get_element_type(elem) not in ALLOWED_SWIMLANES:
                elements.append(elem)
            else:
                elements += self.__flatten(elem)
        return elements

    def run(self):
        try:
            if self.is_json:
                self.model = JsonModel(self.bpmn_model)
                self.__flatten_model()
            else:
                self.model = XmlModel(self.bpmn_model)
            self.__parse()
            self.__mark_gateway_elements()
            if self.transitivity:
                self.__add_transitivity()
            self.validate_splitting_and_joining_gateway_cases()
            return self.sequence
        except Exception:
            logging.warning(
                "\nCould not execute model. Make sure that model is:\n1. Formatted correctly.\n2. File ends with .xml or .json."
            )

    def validate_splitting_and_joining_gateway_cases(self):
        """Update 'is start' and 'is end' attributes of cfo based on splitting/joining gateways.
        Otherwise, the parser interprets the gateways as start/end events instead of the activities.
        """

        item_indices = {item["name"]: index for index, item in enumerate(self.sequence)}
        for cfo in self.sequence:
            if cfo["is start"] and (cfo["type"] in DISCARDED_START_GATEWAYS):
                cfo["is start"] = False
                for successor in cfo["successor"]:
                    self.sequence[item_indices[successor["name"]]]["is start"] = True
            if cfo["is end"] and (cfo["name"] in GATEWAY_NAMES or cfo["type"] == "exclusivegateway"):
                cfo["is end"] = False
                for predecessor in cfo["predecessor"]:
                    self.sequence[item_indices[predecessor["name"]]]["is end"] = True

    def __mark_gateway_elements(self):
        for cfo in self.sequence:
            predecessors = cfo.get("predecessor")
            for predecessor in predecessors:
                predecessor_id = predecessor.get("id")
                predecessor_cfo = self.__get_cfo_by_id(predecessor_id)
                if predecessor_cfo:
                    if predecessor_cfo.get(
                        "type"
                    ) in ALLOWED_GATEWAYS and predecessor_cfo.get("splitting"):
                        cfo.update({"is in gateway": True})
                    if predecessor_cfo.get(
                        "type"
                    ) in ALLOWED_GATEWAYS and predecessor_cfo.get("joining"):
                        continue
                    if cfo.get("type") in ALLOWED_GATEWAYS and cfo.get("joining"):
                        continue
                    if "is in gateway" in predecessor_cfo:
                        cfo.update({"is in gateway": True})

    def __get_cfo_by_id(self, successor_id):
        for cfo in self.sequence:
            if successor_id == cfo.get("id"):
                return cfo

    def __get_parsed_cfo_by_bpmn_element(self, elem):
        elem_id = self.model.get_id(elem)
        for parsed_cfo in self.sequence:
            if parsed_cfo.get("id") == elem_id:
                return parsed_cfo

    def __find_transitive_closure(self, cfo, transitivity):
        if cfo:
            for successor in cfo.get("successor"):
                successor_id = successor.get("id")
                successor = self.__get_cfo_by_id(successor_id)
                if successor:
                    if "is in gateway" not in successor:
                        transitivity.append(successor)
                    for successor in cfo.get("successor"):
                        successor_cfo = self.__get_cfo_by_id(successor.get("id"))
                        self.__find_transitive_closure(successor_cfo, transitivity)

    def __add_transitivity(self):
        for cfo in self.sequence:
            transitivity = []
            self.__find_transitive_closure(cfo, transitivity)
            if transitivity:
                cfo.update({"transitivity": transitivity})

    def __parse(self):
        for elem in self.model.get_diagram_elements():
            cfo = self.__create_cfo(elem)
            if cfo:
                self.sequence.append(cfo)

    def __create_cfo(self, elem):
        if self.__valid_cfo_element(elem):
            successor = self.__get_successors(elem)
            predecessor = self.__get_predecessors(elem)

            cfo = {
                "name": self.__get_label(elem),
                "type": self.model.get_element_type(elem),
                "id": self.model.get_id(elem),
                "successor": self.__format_list(successor),
                "predecessor": self.__format_list(predecessor),
                "is start": len(predecessor) == 0
                or self.__is_predecessor_start_event(predecessor),
                "is end": len(successor) == 0
                or self.__is_successor_end_event(successor),
            }

            if self.__is_element_gateway(elem):
                cfo.update(
                    {
                        "joining": len(self.model.get_outgoing_connection(elem)) == 1,
                        "splitting": len(self.model.get_outgoing_connection(elem)) >= 2,
                    }
                )
            if cfo["successor"]:
                for successor in cfo["successor"]:
                    if successor.get("type") in ALLOWED_GATEWAYS:
                        elem_id = successor.get("id")
                        elem = self.__get_element_by_id(elem_id)
                        gateway_successors = self.__get_successors(elem)
                        successor.update(
                            {
                                "gateway successors": self.__format_list(
                                    gateway_successors, True
                                )
                            }
                        )
            return cfo

    def __valid_cfo_element(self, elem):
        if elem is None:
            return False
        if self.__is_element_activity(elem):
            return True
        if self.__is_element_gateway(elem):
            return True
        if self.__is_element_start_event(elem) and self.__valid_start_name(elem):
            return True
        if self.__is_element_end_event(elem) and self.__valid_end_name(elem):
            return True
        return False

    def __valid_start_name(self, elem):
        try:
            start_name = self.model.get_name(elem)
            if start_name in DISCARDED_START_EVENT_NAMES:
                return False
            if len(start_name.strip()) == 0:
                return False
            if len(start_name) < VALID_NAME_LENGTH:
                return False
            if start_name.isspace():
                return False
        except KeyError:
            return False

    def __valid_end_name(self, elem):
        try:
            end_name = self.model.get_name(elem)
            if end_name in DISCARDED_END_EVENT_NAMES:
                return False
            if len(end_name.strip()) == 0:
                return False
            if len(end_name) < VALID_NAME_LENGTH:
                return False
            if end_name.isspace():
                return False
        except KeyError:
            return False

    def __get_successors(self, elem):
        try:
            connection_objects = self.model.get_outgoing_connection(elem)
            if len(connection_objects) == 0:
                return []
            activities = []
            if isinstance(connection_objects, str):
                connection_objects = [connection_objects]
            for connection in connection_objects:
                if connection:
                    connection_id = (
                        self.model.get_id(connection[0])
                        if isinstance(connection, list)
                        else self.model.get_id(connection)
                    )
                    elem = self.__get_element_by_id(connection_id)
                    if self.model.get_element_type(elem) in ALLOWED_CONNECTING_OBJECTS:
                        connection = self.model.get_outgoing_connection(elem)
                        if connection:
                            elem = (
                                self.__get_element_by_id(
                                    self.model.get_id(connection[0])
                                )
                                if isinstance(connection, list)
                                else self.__get_element_by_id(connection)
                            )
                            activities.append(elem)
            return activities
        except TypeError:
            raise Exception

    def __get_predecessors(self, current_elem):
        predecessors = []
        current_elem_id = self.model.get_id(current_elem)
        try:
            for elem in self.model.get_diagram_elements():
                successors = self.__get_successors(elem)
                if successors:
                    for successor in successors:
                        if successor:
                            if self.model.get_id(successor) == current_elem_id:
                                predecessors.append(elem)
        except Exception:
            raise Exception
        return predecessors

    def __format_list(self, elems, gateway=False):
        formatted = []
        for elem in elems:
            if elem:
                successors = self.__get_successors(elem)
                cfo = {
                    "name": self.__get_label(elem),
                    "type": self.model.get_element_type(elem),
                    "id": self.model.get_id(elem),
                    "gateway successor": gateway,
                    "splitting": len(successors) >= 2,
                    "is end": len(successors) == 0
                    or self.__is_successor_end_event(successors),
                }

                try:
                    cfo.update({"splitting": len(self.__get_successors(elem)) >= 2})
                except Exception:
                    pass
                formatted.append(cfo)
        return formatted

    def __get_element_by_id(self, connection_id):
        try:
            return next(
                e
                for e in self.model.get_diagram_elements()
                if self.model.get_id(e) == connection_id
            )
        except StopIteration:
            raise Exception(f"Could not find element with ID {connection_id}")

    def __get_activity_type(self, elem):
        return ACTIVITY_MAPPING.get(self.model.get_element_type(elem), "Activity")

    def __get_gateway_type(self, elem):
        return GATEWAY_MAPPING.get(self.model.get_element_type(elem), "Gateway")

    def __get_end_type(self, elem):
        return END_EVENT_MAPPING.get(self.model.get_element_type(elem), "EndEvent")

    def __get_label(self, elem):
        try:
            if self.__is_element_activity(elem):
                try:
                    return self.sanitizer.sanitize_label(self.model.get_name(elem))
                except KeyError:
                    return self.__get_activity_type(elem)
            if self.__is_element_gateway(elem):
                try:
                    return self.sanitizer.sanitize_label(self.model.get_name(elem))
                except KeyError:
                    return self.__get_gateway_type(elem)
            if self.__is_element_start_event(elem) or self.__is_element_end_event(elem):
                try:
                    return self.sanitizer.sanitize_label(self.model.get_name(elem))
                except KeyError:
                    return self.model.get_element_type(elem)
        except KeyError:
            return self.model.get_element_type(elem)

    def __is_element_start_event(self, elem):
        return self.model.get_element_type(elem) in ALLOWED_START_EVENTS

    def __is_element_end_event(self, elem):
        return self.model.get_element_type(elem) in ALLOWED_END_EVENTS

    def __is_element_activity(self, elem):
        return self.model.get_element_type(elem) in ALLOWED_ACTIVITIES

    def __is_element_gateway(self, elem):
        return self.model.get_element_type(elem) in ALLOWED_GATEWAYS

    def __is_predecessor_start_event(self, predecessors):
        for predecessor in predecessors:
            if predecessor:
                predecessor_type = self.model.get_element_type(predecessor)
                if (
                    predecessor_type in ALLOWED_START_EVENTS
                    and predecessor_type not in DISCARDED_START_EVENT_NAMES
                ):
                    if self.__valid_start_name(predecessor):
                        return False
                    return True
        return False

    def __is_successor_end_event(self, successors):
        for successor in successors:
            if successor:
                if self.model.get_element_type(successor) in ALLOWED_END_EVENTS:
                    if self.__valid_end_name(successor):
                        return False
                    return True
        return False

    def count_parsable_elements(self):
        count = 0
        for elem in self.model.get_diagram_elements():
            elem_type = self.model.get_element_type(elem)
            if elem_type in ALLOWED_ACTIVITIES or elem_type in ALLOWED_GATEWAYS:
                count += 1
        return count

    def count_model_elements(self):
        return len(self.bpmn_model[CHILD_SHAPES])

    def count_model_element_types(self):
        return len(self.get_element_types())

    def count_pools(self):
        count = 0
        for elem in self.bpmn_diagram[CHILD_SHAPES]:
            if self.model.get_element_type(elem) == "Pool":
                count += 1
        return count

    def has_start(self):
        return any(elem.get("is start") for elem in self.sequence)

    def get_element_types(self):
        elem_types = {}

        for elem in self.model.get_diagram_elements():
            elem_type = self.model.get_element_type(elem)

            if elem_type in elem_types:
                elem_types[elem_type] += 1
            else:
                elem_types[elem_type] = 1
        return elem_types

    def contains_multiple_starts(self):
        count = 0
        for elem in self.model.get_diagram_elements():
            if self.__is_element_start_event(elem):
                count += 1
        return count > 1

    def or_multiple_paths(self):
        for elem in self.model.get_diagram_elements():
            if (
                self.model.get_element_type(elem) == "InclusiveGateway"
                and len(self.model.get_outgoing_connection(elem)) >= 3
            ):
                return True
        return False
