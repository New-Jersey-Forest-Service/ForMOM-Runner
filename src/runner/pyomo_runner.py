'''
Pyomo Runner

Contains functions to
 - build linear optimziation problems from data
 - run the solver
 - extract info from solved instances

Data can be a .dat file or a dictionary with the
relevant info.

New Jersey Forest Service 2022
'''
import sys
from typing import Any, Dict, Union
import pyomo.environ as pyo
import pyomo.opt as opt

import runner.text as text


# In Python2, integer divisions truncate values (1/2 = 0 instead of 0.5)
# which breaks the solver. Either way, we should be using python3
if (sys.version[0] != '3'):
	print("You are not using python 3, so this will fail")
	sys.exit(1)







# =====================================================================================
#                           Setting up and Running a Model
# =====================================================================================


# Really this abstract model should be built once at init
# instead of by calling a function, but the overhead is so low
# it doesn't really matter.
def _buildAbstractModel () -> pyo.AbstractModel:
	# Build the model
	model = pyo.AbstractModel()
	model.index_vars = pyo.Set()
	model.index_le_consts = pyo.Set()
	model.index_ge_consts = pyo.Set()
	model.index_eq_consts = pyo.Set()

	model.x = pyo.Var(model.index_vars, domain=pyo.NonNegativeReals)

	# These guys are read from input.dat
	model.vec_objective = pyo.Param(model.index_vars)

	model.mat_le = pyo.Param(model.index_le_consts, model.index_vars)
	model.vec_le = pyo.Param(model.index_le_consts)

	model.mat_ge = pyo.Param(model.index_ge_consts, model.index_vars)
	model.vec_ge = pyo.Param(model.index_ge_consts)

	model.mat_eq = pyo.Param(model.index_eq_consts, model.index_vars)
	model.vec_eq = pyo.Param(model.index_eq_consts)

	#Defining the actual functions
	def obj_function(_model):
		return pyo.summation(_model.vec_objective, _model.x)

	def le_mat_rule (_model, k):
		return sum(_model.mat_le[k, i] * _model.x[i] for i in _model.index_vars) <= _model.vec_le[k]

	def ge_mat_rule (_model, k):
		return sum(_model.mat_ge[k, i] * _model.x[i] for i in _model.index_vars) >= _model.vec_ge[k]

	def eq_mat_rule (_model, k):
		return sum(_model.mat_eq[k, i] * _model.x[i] for i in _model.index_vars) == _model.vec_eq[k]

	model.OBJ = pyo.Objective(rule=obj_function, sense=pyo.maximize)
	model.GEConstraint = pyo.Constraint(model.index_ge_consts, rule=ge_mat_rule)
	model.LEConstraint = pyo.Constraint(model.index_le_consts, rule=le_mat_rule)
	model.EQConstraint = pyo.Constraint(model.index_eq_consts, rule=eq_mat_rule)

	return model


def loadPyomoModelFromDataDict (datadict: dict):
	model = _buildAbstractModel()
	instance = model.create_instance(data=datadict)
	instance.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT)
	return instance


def loadPyomoModelFromDat (datFilepath: str) -> pyo.ConcreteModel:
	model = _buildAbstractModel()

	# Now read data file
	instance = model.create_instance(filename=datFilepath)

	# Add duals (shadow cost) info 
	# I have no idea why duals are the same as shadow costs, but they are
	instance.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT)

	return instance


def solveConcreteModel (instance: pyo.ConcreteModel, verboseToConsole: bool=False) -> Union[pyo.ConcreteModel, opt.SolverResults]:
	'''
		Solves the passed in modle (mutates it), and returns
		the concrete model + the solver results
	'''
	print("Solving a model", end='')
	solver = pyo.SolverFactory('glpk')

	# Now optimize
	results = solver.solve(instance, tee=verboseToConsole)
	print(" ... Solved")

	return instance, results


















# =====================================================================================
#                            Extracting Information from a Run
# =====================================================================================



# For all of this extraction info (what are shadow prices, slacks, etc)
# Pg. 14 - 22 of this textbook on optimization are really handy http://web.mit.edu/15.053/www/AMP-Chapter-01.pdf
#
# For getting shadow prices, see
# https://stackoverflow.com/questions/65523319/pyomo-accesing-retrieving-dual-variables-shadow-price-with-binary-variables


def isModelSolved (results: opt.SolverResults) -> bool:
	'''
	Returns whether the model is solved (optimal).

	If the model did not terminate optimally, it's not guaranteed
	you can read information from it (slacks, var values, etc)
	'''
	return results.solver.termination_condition == 'optimal'


def getRunSummary (instance: pyo.ConcreteModel, results: opt.SolverResults) -> Dict[str, Any]:
	'''
	Returns a dict of run attributes. If an attribute is impossible to get (eg: run not solved)
	then the value is set to None.
	{
		'termination': 'optimal',
		'objective_value': 43243,
		    ...
	}
	'''
	status = str(results.solver.status)
	termination = str(results.solver.termination_condition)
	obj_value = None

	if termination == 'optimal':
		obj_value = pyo.value(instance.OBJ)
	
	return {
		'status': status,
		'termination': termination,
		'objective_value': obj_value
	}


def getVariableValues (instance: pyo.ConcreteModel, hideDummy=True) -> Dict[str, float]:
	'''
		Returns a dict of variable names as keys and values as entries
		{'167N_PLSQ_2021': 34343, ... }

		hideDummy = True means it will hide variables with dummy in the name
	'''
	decisionVars = instance.x.keys()
	if hideDummy:
		decisionVars = filter(lambda s: 'dummy' not in s, decisionVars)
	
	return {
		str(key): pyo.value(instance.x[key]) 
		for key in decisionVars
		}


def getShadowPrices (instance: pyo.ConcreteModel, hideDummy=True) -> Dict[str, float]:
	'''
		Returns a dict of {constraint_name: shadow price}

		hideDummy = True means it will hide variables with dummy in the name
	'''
	constNames = instance.dual.keys()
	if hideDummy:
		constNames = filter(lambda s: 'dummy' not in str(s), constNames)

	return {
		str(key).split("[")[1][:-1]: instance.dual[key] 
		for key in constNames
		}


def getSlackGE (instance: pyo.ConcreteModel, hideDummy=True) -> Dict[str, float]:
	'''
		Returns a dict of {GEConstraintName: slack amount}

		hideDummy = True means it will hide variables with dummy in the name
	'''
	geConstNames = instance.GEConstraint.keys()
	if hideDummy:
		geConstNames = filter(lambda s: 'dummy' not in s, geConstNames)
	
	return {
		str(key): instance.GEConstraint[key].lslack() 
		for key in geConstNames
		}


def getSlackLE (instance: pyo.ConcreteModel, hideDummy=True) -> Dict[str, float]:
	'''
		Returns a dict of {LEConstraintName: slack amount}

		hideDummy = True means it will hide variables with dummy in the name
	'''
	leConstNames = instance.LEConstraint.keys()
	if hideDummy:
		leConstNames = filter(lambda s: 'dummy' not in s, leConstNames)
	
	return {
		str(key): instance.LEConstraint[key].uslack() 
		for key in leConstNames
		}





if __name__ == '__main__':
	filepath = '/home/velcro/Documents/Professional/NJDEP/TechWork/ForMOM-Runner/sample-data/SLmonthly1_out.dat'
	instance = loadPyomoModelFromDat(filepath)
	instance, res = solveConcreteModel(instance)
	resStr = text.exportRunText(instance, res)

	print(resStr)

