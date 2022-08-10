'''
Export.py

This file handles all exporting. Pass in names, results, instances and this will
write to files.
'''

import os
import pathlib
from typing import Union, List, Tuple, Optional
import pyomo.environ as pyo
import pyomo.opt as opt

import runner.text as text



# =====================================================================================
#                                   High Level Exporting Calls
# =====================================================================================

def exportSingleAsTXT (outfile, 
                    instance: pyo.ConcreteModel, 
                    result: opt.SolverResults,
                    verify_successful=False) -> int:
    '''
    Converts a run into a single .txt file

    If verify_successful = True, it checks for the status to be 'ok'.

    Returns the number of files written (0 or 1)
    '''
    if verify_successful:
        status = result.solver.status
        if status != 'ok':
            return 0

    runOut = text.exportRunText(instance, result)

    with open(outfile, 'w') as f:
        f.write(runOut)
    
    return 1
 

def exportManyAsTXT (outfolder,
                    runNames: List[str],
                    instances: List[pyo.ConcreteModel],
                    results: List[opt.SolverResults],
                    verify_successful=False) -> int:
    '''
    Converts parallel lists of instances and results to file files.

    Attempts to create a folder within the specified directory

    If verify_successful = True, it checks for the status to be 'ok'.

    Returns the number of files written. -1 means error.
    '''
    print("Tying to export")
    numExport = 0

    # Step 1: Create sub directory
    if _isInvalidDir(outfolder):
        return -1
    print("Is valid directory")

    outDir = pathlib.Path(outfolder)
    time_str = text.getTimestamp()
    subdir = f'RunOutput-{time_str}'
    outDir = outDir.joinpath(subdir)

    print(f"Trying to make {outDir}")

    try:
        os.mkdir(outDir)
    except Exception:
        return -1
    print("Did make directory")

    for name, inst, res in zip(runNames, instances, results):
        runName = text.FILE_OUTTXT_PREFIX + name
        runPath = outDir.joinpath(runName)

        succ = exportSingleAsTXT(runPath, inst, res, verify_successful=verify_successful)
        if succ > 0:
            numExport += 1

    return numExport


def exportSingleAsCSVs (outfile, 
                    instance: pyo.ConcreteModel, 
                    result: opt.SolverResults,
                    verify_successful=False) -> int:
    '''
    Converts a single run to multiple .csvs

    If verify_successful = True, it checks for the status to be 'ok'.

    Returns the number of files written (0 or 1)
    '''

    if verify_successful:
        status = result.solver.status
        if status != 'ok':
            return
    
    # TODO









# =====================================================================================
#                               Intermediate Processing Functions
# =====================================================================================










# Util

def _isInvalidDir(dialogOutput) -> bool:
	return dialogOutput == None or type(dialogOutput) != str or dialogOutput.strip() == ""


