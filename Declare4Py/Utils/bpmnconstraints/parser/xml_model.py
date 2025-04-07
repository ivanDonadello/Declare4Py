from Declare4Py.Utils.bpmnconstraints.utils.constants import *
from xml.etree import ElementTree
import xmltodict as xtd

PROCESS_ELEMENT = ".//{http://www.omg.org/spec/BPMN/20100524/MODEL}process"


class XmlModel:
    def __init__(self, model) -> None:
        self.root = model
        self.process_elements = self.root.find(PROCESS_ELEMENT)
        self.child_elements = self.process_elements.findall("./*")

    def __xml_to_dict(self, input_dict):
        new_dict = {}
        new_dict["outgoing"] = []
        for tag_key in input_dict:
            new_dict["type"] = tag_key.split(":")[1]
            for key, value in input_dict[tag_key].items():
                if key in ["ns0:extensionElements"]:
                    continue
                if key.startswith("@"):
                    new_dict[key[1:]] = value
                elif key.endswith(":outgoing"):
                    if isinstance(value, list):
                        new_dict["outgoing"].extend(value)
                    else:
                        new_dict["outgoing"].append(value)
                else:
                    new_dict[key] = value
        return new_dict

    def get_child_models(self):
        elements = []

        for child in self.child_elements:
            xml_string = ElementTree.tostring(child, encoding="utf-8")
            parsed_xml = self.__xml_to_dict(xtd.parse(xml_string))
            if parsed_xml["type"] == "extensionElements":
                continue
            elements.append(parsed_xml)
        return elements

    def get_element_type(self, elem):
        return elem["type"].lower()

    def get_diagram_elements(self):
        try:
            return self.get_child_models()
        except KeyError:
            raise Exception("Could not find any child elements to diagram.")

    def get_outgoing_connection(self, elem):
        if elem["type"] == "sequenceFlow":
            return elem["targetRef"]
        return elem["outgoing"]

    def get_name(self, elem):
        try:
            return elem["name"]
        except KeyError:
            return elem["type"].lower()

    def get_id(self, elem):
        if isinstance(elem, str):
            return elem
        return elem["id"]
