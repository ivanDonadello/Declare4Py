from Declare4Py.Utils.bpmnconstraints.utils.constants import *

class JsonModel:
    def __init__(self, model) -> None:
        self.model = model

    def get_child_models(self):
        return self.model[CHILD_SHAPES]

    def get_element_type(self, elem):
        return elem[STENCIL][ID].lower()

    def get_diagram_elements(self):
        try:
            return self.get_child_models()
        except KeyError:
            raise Exception("Could not find any child elements to diagram.")

    def get_outgoing_connection(self, elem):
        return elem[OUTGOING]

    def get_name(self, elem):
        return elem[PROPERTIES][NAME]

    def get_id(self, elem):
        return elem[ELEMENT_ID]
