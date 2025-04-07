import io
import logging
import sys
import json
from pathlib import Path
from tqdm import tqdm
from Declare4Py.Utils.bpmnconstraints.parser.bpmn_parser import Parser
from Declare4Py.Utils.bpmnconstraints.compiler.bpmn_compiler import Compiler
from Declare4Py.ProcessModels.DeclareModel import DeclareModel
from Declare4Py.ProcessModels.LTLModel import LTLModel
from Declare4Py.ProcessModels.AbstractModel import ProcessModel
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class BpmnConstraintsModel(ProcessModel):
    """
    BpmnConstraintsModel is designed to extract constraints from a bpmn diagram expressed as a xml file.
    For example usage, see Declare4Py/Utils/bpmnconstraints/tutorial/bpmn2constraints.ipynb
    """
    def __init__(self):
        super().__init__()
        self.declare_model = DeclareModel()
        self.ltl_model = []
        self.formulas = []
        self.serialized_constraints: [str] = []

    def parse_from_file(self, model_path: str, **kwargs):
        """

        Uses a path to a xml file to parse and create a DeclareModel and a LTLModel for Declare4Py

        arguments: 
            modelpath - The path to the xml file, as a string
            kwargs - 
        """
        xml_path = Path(model_path)

        # Check if the path is a file
        if not xml_path.is_file():
            logging.warning("Provided path is not a file: {}".format(model_path))
            return
        try:
            # Parsing and compiling the BPMN constraints
            parsed_result = Parser(xml_path, True, transitivity=False).run()
            compiled_result = Compiler(parsed_result, transitivity=True, skip_named_gateways=False).run()

            # Extract DECLARE and LTLf constraints
            declare_constraints = [constraint.get("DECLARE") for constraint in compiled_result]
            ltl_constraints = [constraint.get("LTLf") for constraint in compiled_result]

            # Assign the constraints to the class attributes if they exist
            if declare_constraints and ltl_constraints:
                self.declare_model = self.declare_model.parse_from_diagram(declare_constraints)
                for con in ltl_constraints:
                    if con is not None:
                        ltl_model = LTLModel()
                        ltl_model.parse_from_diagram(con, self.declare_model.activities)
                        self.ltl_model.append(ltl_model)
                    
                
        except Exception as e:
            logging.error(f"{model_path}: {e}")
        
    def parse_from_string(self, content: str, **kwargs):
        declare_constraints = []
        ltl_constraints = []
        
        # Convert string content to a StringIO object to mimic a file-like object
        xml_io = io.StringIO(content)
        
        try:
            # Parse and compile the BPMN constraints from the string
            result = Parser(xml_io, True, transitivity=False).run()
            result = Compiler(result, transitivity=False, skip_named_gateways=False).run()
            
            # Extract DECLARE and LTLf constraints
            for constraint in tqdm(result):
                declare_constraints.append(constraint.get("DECLARE"))
                ltl_constraints.append(constraint.get("LTLf"))
                
            # Assign the parsed constraints to the class attributes
            if declare_constraints:
                self.declare_model = declare_constraints
            self.ltl_model = ltl_constraints
        except Exception as e:
            logging.error(f"Error parsing from string: {e}")

    def to_file(self, model_path: str, **kwargs):
        data = {
            "declare_model": self.declare_model,
            "ltl_model": self.ltl_model
        }
        with open(model_path, 'w') as file:
            json.dump(data, file, indent=4)
        logging.info(f"Model saved to {model_path}")

    def set_constraints(self):
        """Sets the constraints for the Declare model"""
        for constraint in self.constraints:
            constraint_str = constraint['template'].templ_str
            if constraint['template'].supports_cardinality:
                constraint_str += str(constraint['n'])
            constraint_str += '[' + ", ".join(constraint["activities"]) + '] |' + ' |'.join(constraint["condition"])
            self.serialized_constraints.append(constraint_str)