'''
Text

This file contains constants and functions revolving text
 - Splash screen message
 - All large status messages (placed into the status box)
 - Export strings
 - Constants

Ideally the text constants would be in a .toml or .json but I didn't want to deal
with reading a file from within the .pyz. If we ever need translations this is 
still a good start.
'''
import pyomo.environ as pyo
import pyomo.opt as opt
import time
from typing import List, Optional, Set

import runner.model_data_classes as models
import runner.pyomo_runner as pyomo_runner


# The string displayed when the program boots
SPLASH_STRING = '	 \n\n\n			888\'Y88	\n			888 ,\'Y  e88 88e  888,8,\n			888C8   d888 888b 888 " \n			888 "   Y888 888P 888   \n			888	  "88 88"  888   \n \n		 e   e	   e88 88e	   e   e\n		d8b d8b	 d888 888b	 d8b d8b\n	   e Y8b Y8b   C8888 8888D   e Y8b Y8b\n	  d8b Y8b Y8b   Y888 888P   d8b Y8b Y8b\n	 d888b Y8b Y8b   "88 88"   d888b Y8b Y8b\n\n  \n'

NO_FILE_SEL = 'No File Selected'

BTNOBJ_SINGLE = 'Objective .csv'
BTNOBJ_DIR = 'Objectives Folder'

BTNSAVE_SINGLE = 'Save Output to File'
BTNSAVE_DIR = 'Save Output to Folder'

BTNRUN_SINGLE = 'Run Model'
BTNRUN_MANY = 'Run All Models'


FILE_OUTTXT_PREFIX = 'rawPyoOut_'



def getTimestamp () -> str:
	cur_time = time.localtime(time.time())
	time_str = "{Year}-{Month}-{Day}-{Hour}-{Min}-{Sec}".format(
		Year=cur_time.tm_year, 
		Month=str(cur_time.tm_mon).zfill(2),  # zfill pads the string with zeros
		Day=str(cur_time.tm_mday).zfill(2),   # i.e. "3" -> "03"
		Hour=str(cur_time.tm_hour).zfill(2),
		Min=str(cur_time.tm_min).zfill(2),
		Sec=str(cur_time.tm_sec).zfill(2)
	)
	return time_str



def statusLoadMany (errFiles: List[str], 
					warnFiles: List[str], 
					perfectFiles: List[str], 
					errFound: Set[str], 
					warnFound: Set[str]) -> str:
	rStr = ""

	nPerf = len(perfectFiles)
	nWarn = len(warnFiles)
	nErr = len(errFiles)

	nLoaded = nPerf + nWarn

	# Two ways to have an error
	if nPerf + nWarn + nErr == 0:
		rStr += "[[ Error ]]\n"
		rStr += "No .csv files found in directory"
	elif nLoaded == 0:
		rStr += "[[ Error ]]\n"
		rStr += "All objective files loaded with errors."
	else:
		rStr += "[[ Success ]]\n"
		rStr += "At least one objective file worked"

	rStr += "\n\n"

	# Give summary numbers
	rStr += f"Total Loaded: {nLoaded}\n" + \
					f" - perfectly: {nPerf}\n" + \
					f" - with warning: {nWarn}\n" + \
					f"Total Errored: {nErr}\n"

	# Report file names
	_sortedPerfect = sorted(perfectFiles) # Sorted returns a copy
	_sortedWarn = sorted(warnFiles)       # so no side effects of input
	_sortedErr = sorted(errFiles)

	rStr += "\n\n === Files Loaded Perfectly ==="
	rStr += "\n ~ ".join([''] + _sortedPerfect)

	rStr += "\n\n === Files Loaded with Warnings ==="
	rStr += "\n ! ".join([''] + _sortedWarn)

	rStr += "\n\n === Files with Errors ==="
	rStr += "\n x ".join([''] + _sortedErr)
	rStr += "\n\n\n\n"

	# Report erros and warnings
	if len(warnFound) != 0:
		rStr += "\n!!!! Warnings found !!!!"
		rStr += "\n\n[[ Warning ]]\n".join([''] + list(warnFound))

	if len(errFound) != 0:
		rStr += "\n\n\nXXXX Errors found XXXX"
		rStr += "\n\n[[ Error ]]\n".join([''] + list(errFound))
	
	return rStr


def statusLoadSingle (objData: models.InputObjectiveData, messages: Optional[List[str]]) -> str:
	rStr = ''

	if objData == None:
		rStr = "XXXXXX\n[[ Errors Occured - Unable to Convert ]]\n" + \
			   "\n\n[[ Error ]]\n".join([''] + messages)
	else:
		rStr = "[[ Conversion Success ]]\n"
		if len(messages) > 1:
			rStr += "\n\n[[ Warning ]]\n".join([''] + messages)
	
	return rStr


def statusRunMany (names: List[str], results: List[opt.SolverResults]) -> str:
	'''
	The string to show after running many models
	'''
	# First sort by successful vs unsuccessful
	succ_names = []
	succ_terms = []
	fail_names = []
	fail_terms = []

	for name, res in zip(names, results):
		status = res.solver.status
		termination = res.solver.termination_condition

		if status == 'ok':
			succ_names.append(name)
			succ_terms.append(termination)
		else:
			fail_names.append(name)
			fail_terms.append(termination)
	
	# Now build the string
	rStr = ''

	rStr += " === Successful Runs ===\n"
	for name, term in zip(succ_names, succ_terms):
		rStr += f"{name}  |  {term}\n"
	rStr += "\n" * 3

	rStr += " === Failed Runs ===\n"
	for name, term in zip(fail_names, fail_terms):
		rStr += f"{name}  |  {term}\n"

	return rStr


def statusRunSingle (instance: pyo.ConcreteModel, results: opt.SolverResults) -> str:
	'''
	The string to show after running a single model
	'''
	return " == Ran Single Model ==\n\n" + \
		exportRunText(instance, results)


def statusSaveMany (outdir: str, numWritten: int) -> str:
	if numWritten == -1:
		return "[[ XX Error ]]\n\n" + \
			  f"Attempted to write to\n{outdir}\n\n" + \
			  f"Invalid directory, or subdirectory already exists, or something else weird :/"
	else:
		return f"[[ Success ]]\nWrote {numWritten} files to {outdir}"


def statusSaveSingle (outdir: str) -> str:
	return f"[[ Success ]]\n\nWrote to file {outdir}"





def guiLoadedModelsSummary (loadedModels: List[models.FinalModel]) -> str:
	sampleLM = loadedModels[0]
	num_vars = len(sampleLM.var_names)
	num_consts = len(sampleLM.eq_vec) + len(sampleLM.ge_vec) + len(sampleLM.le_vec)

	model_str = \
		f"Model Loaded\n" + \
		f"{num_vars} variables, {num_consts} constraints\n" + \
		f"EQ: {len(sampleLM.eq_vec)} | GE: {len(sampleLM.ge_vec)} | LE: {len(sampleLM.le_vec)}\n" + \
		f"Objectives Loaded: {len(loadedModels)}"

	return model_str




def exportRunText (instance: pyo.ConcreteModel, results: opt.SolverResults) -> str:
	rstr = ''

	# Check status of model
	status = results.solver.status
	termination_cond = results.solver.termination_condition

	# List of possible status & term conditions
	# https://github.com/Pyomo/pyomo/blob/main/pyomo/opt/results/solver.py

	rstr += f"Solve attempted\n"
	rstr += f"Status: {status}\n"
	rstr += f"Termination Condition: {termination_cond}\n"
	rstr += "\n" * 5

	if (termination_cond != pyo.TerminationCondition.optimal):
		rstr += " [[ ERROR ]]: Solve ended without optimal solution\n"
		rstr += "\taborting"
		return rstr


	# Get values
	decvars_values = pyomo_runner.getVariableValues(instance)
	shadow_prices = pyomo_runner.getShadowPrices(instance)
	ge_slack = pyomo_runner.getSlackGE(instance)
	le_slack = pyomo_runner.getSlackLE(instance)

	shadow_keys = list(shadow_prices.keys())
	ge_keys = list(ge_slack.keys())
	le_keys = list(le_slack.keys())


	# Now actual output
	rstr += "\n\n == Variables\n"
	rstr += "\n".join(["%-20s | %s" % (k, decvars_values[k]) for k in decvars_values])

	rstr += "\n\n == Shadow Prices\n"
	rstr += "\n".join(["%-40s | %s" % (k, shadow_prices[k]) for k in shadow_keys])

	rstr += "\n\n == Slacks for GE\n"
	rstr += "\n".join(["%-40s | %s" % (k, ge_slack[k]) for k in ge_keys])

	rstr += "\n\n == Slacks for LE\n"
	rstr += "\n".join(["%-40s | %s" % (k, le_slack[k]) for k in le_keys])

	return rstr







# Everything in this file should be of string return type

