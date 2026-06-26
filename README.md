# Declare4Py

Declare4Py is the first Python package for declarative Process Mining with core functionalities to 
easily implement Machine Learning applications for Process Mining. Declarative process mining uses 
declarative behavioural rules (based on Linear Temporal Logic on finite traces) for defining process models. This 
results in a high flexibility of the business process model definition without neglecting hard 
constraints that must be satisfied. Moreover, declarative languages can be used as a bridge between 
Process Mining and Machine learning with the DECLARE encoding that encodes the traces in a log into a 
numeric format suitable as input to Machine Learning algorithms. Declare4Py implements such a bridge 
by including standard algorithms for:

1. declarative Process Mining with LTLf or (MP)-DECLARE templates (e.g., conformance checking, model discovery, trace generation, query checking);
2. log encodings (e.g., complex-index, aggregate, Declare);
3. log labelling according to filtering or declarative rules.

All the Declare4Py data formats are compatible with the main Machine Learning Python packages: scikit-learn, Tensorflow and PyTorch.


## Installation
We recommend using a virtual environment to avoid conflicts with your local Python packages. You can create one with [Conda](https://conda.io/projects/conda/en/latest/index.html) or Python's [venv](https://docs.python.org/3/library/venv.html) utility.

### 1. Create a Virtual Environment
Using Conda:

```bash
conda create -n declare4py python=3.10
conda activate declare4py
```

Using venv:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. Install Declare4Py
Choose one installation method.

From **PyPI**:

```bash
pip install declare4py
```

From **source**, for local development:

```bash
git clone https://github.com/ivanDonadello/Declare4Py.git
cd Declare4Py
pip install -e .
```

The editable install also installs the package dependencies declared by the project. If you only need the dependencies without installing Declare4Py itself, run:

```bash
pip install -r requirements.txt
```

### 3. Install the Lydia Backend
The [Lydia](https://github.com/whitemech/lydia) backend for the LTLf conformance checking needs to be installed with Docker:

1. Install [Docker](https://www.docker.com/get-started/).

2. Download the Lydia Docker image:

   ```bash
   docker pull whitemech/lydia:latest
   ```

3. Make the Docker image executable under the name `lydia`.

   3.1. Install with **Linux or macOS**:

   ```bash
   echo '#!/usr/bin/env sh' > lydia
   echo 'docker run -v$(pwd):/home/default whitemech/lydia lydia "$@"' >> lydia
   sudo chmod u+x lydia
   sudo mv lydia /usr/local/bin/
   ```

   3.2. Install with **Windows**:
   Create a `lydia.bat` file in a directory included in your `PATH` with the following content:

   ```bat
   @echo off
   docker run -v "%cd%:/home/default" whitemech/lydia lydia %*
   ```

More information can be found [here](https://github.com/whitemech/logaut).


## Tutorials
The `docs/source/tutorials/` folder contains a walk-through of Declare4Py. In order, the tutorials cover the following topics:

1. [Managing event logs](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/1.Managing_Event_Logs.ipynb): methods to manage event logs, importing them, extracting useful information, converting them in other formats;
2. [Managing process models](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/2.Managing_Process_Models.ipynb): simple methods to parse and manage process models from strings and/or files and checking their satisfiability;
3. [Conformance checking of LTLf templates/formulas](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/3.Conformance_checking_LTLf.ipynb): check what are the traces in an event log that satisfy a given LTLf model; 
4. [Conformance checking of MP-DECLARE templates](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/4.Conformance_checking_DECLARE.ipynb): check what are the traces in an event log (along with the fulfillments/violations) that satisfy a given MP_DECLARE model;
5. [Query Checking with DECLARE models](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/5.Declare_Query_Checking.ipynb): discover what are the activities that make an input DECLARE constraint satisfied in an event log;
6. [Discovery of DECLARE models from event logs](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/6.Declare_Model_Discovery.ipynb): discover what are the most satisfied DECLARE constraints in an event log;
    1. [Discovery of DECLARE models from text](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/6.1.Textual_Declare_Model_Discovery.ipynb): discover a DECLARE model from text specification with the use of Large Language Models.
7. [Filtering an event log](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/7.Log_filtering.ipynb): select a subset of an event log that satisfy some input properties;
8. [Log encodings](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/8.Log_Encodings.ipynb): convert an event log in a numerical matrix for machine learning oriented applications;
9. [Log generation with a MP-DECLARE model](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/9.ASP_Log_Generation.ipynb): generate synthetic cases that satisfy an MP-DECLARE model;

The tutorials are Jupyter notebooks and consider the [Sepsis cases log](https://data.4tu.nl/articles/dataset/Sepsis_Cases_-_Event_Log/12707639).

## Repository Structure
- `Declare4Py/ProcessModels` -- the implementation of the supported process models.
- `Declare4Py/ProcessMiningTasks/` -- the implementation of the supported Process Mining tasks.
- `tests/` -- a collection of tests for computing the Declare4Py performance.
- `docs/source/tutorials/` -- tutorials to start with Declare4Py,

## Citing Declare4Py
If you use Declare4Py in your research, please use the following BibTeX entry.

```
@inproceedings{DonadelloRMS22,
  author    = {Ivan Donadello and
               Francesco Riva and
               Fabrizio Maria Maggi and
               Aladdin Shikhizada},
  title     = {Declare4Py: {A} Python Library for Declarative Process Mining},
  booktitle = {{BPM} (PhD/Demos)},
  series    = {{CEUR} Workshop Proceedings},
  volume    = {3216},
  pages     = {117--121},
  publisher = {CEUR-WS.org},
  year      = {2022}
}
```

