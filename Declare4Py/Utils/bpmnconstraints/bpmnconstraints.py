import logging
import sys
from pathlib import Path
from json import dumps
from tqdm import tqdm
from Declare4Py.bpmnconstraints.parser.bpmn_parser import Parser
from Declare4Py.bpmnconstraints.compiler.bpmn_compiler import Compiler
from Declare4Py.bpmnconstraints.utils.script_utils import Setup
from Declare4Py.bpmnconstraints.script_utils.constraint_comparison import ComparisonScript
from Declare4Py.bpmnconstraints.script_utils.dataset_parsing import ParserScript
from Declare4Py.bpmnconstraints.script_utils.dataset_compiling import CompilingScript

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def bpmnconstraints(parse_path=None, compile_path=None, transitivity=False, compare_constraints=None,
                    dataset=None, dataframe=None, parse_dataset=None, plot=False,
                    constraint_type="DECLARE", compile_dataset=None, skip_named_gateways=False):
    """
    Main function for BPMN2Constraints tool. At least one flag should be set.

    Parameters:
    - parse_path (str): Path to the BPMN file to parse.
    - compile_path (str): Path to the BPMN file to compile.
    - transitivity (bool): Flag for transitivity in compilation.
    - compare_constraints (bool): Flag for comparing constraints.
    - dataset (str): Path to the dataset for comparison.
    - dataframe (str): Path to the dataframe of compiled constraints for comparison.
    - parse_dataset (str): Path to the dataset folder for parsing.
    - plot (bool): Flag for generating plots.
    - constraint_type (str): Type of constraint to be generated ("DECLARE" or "LTLf").
    - compile_dataset (str): Path to the dataset folder for compilation.
    - skip_named_gateways (bool): Flag to skip adding gateways as tokens in compilation.

    Returns:
    - list or dict: Depending on the operation, returns a list of constraints or the result of the operation.
    """
    constraints = []
    if parse_path:
        path = Path(parse_path)
        setup = Setup(None)
        if setup.is_file(path):
            result = Parser(path, True, transitivity).run()
            if result:
                print(dumps(result, indent=2))

    elif compile_path:
        path = Path(compile_path)
        setup = Setup(None)
        if setup.is_file(path):
            result = Parser(path, True, transitivity).run()
            result = Compiler(result, transitivity, skip_named_gateways).run()
            if constraint_type == "LTLf":
                for constraint in tqdm(result):
                    constraints.append(constraint.get("LTLf"))
            elif constraint_type == "DECLARE":
                for constraint in tqdm(result):
                    constraints.append(constraint.get("DECLARE"))
            else:
                logging.warning(
                    "Unknown constraint type. 'DECLARE' or 'LTLF'."
                )
            if result:
                return constraints

    elif compare_constraints:
        if dataset is None or dataframe is None:
            logging.warning("If invoking compare_constrains, include path to dataset and dataframe")
        dataframe_path = Path(dataframe)
        dataset_path = Path(dataset)
        setup = Setup(None)
        if setup.is_file(dataframe_path) and setup.is_file(dataset_path):
            script = ComparisonScript(dataset_path, dataframe_path, plot)
            script.run()

    elif parse_dataset:
        dataset_path = Path(parse_dataset)
        setup = Setup(None)
        if setup.is_directory(dataset_path):
            script = ParserScript(dataset_path, plot)
            script.run()

    elif compile_dataset:
        dataset_path = Path(compile_dataset)
        setup = Setup(None)
        if setup.is_directory(dataset_path):
            script = CompilingScript(dataset_path, transitivity, False)
            script.run()

    else:
        print("Invalid or missing arguments.")
