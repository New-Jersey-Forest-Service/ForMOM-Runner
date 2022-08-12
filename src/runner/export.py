'''
Export.py

This file handles all exporting. Pass in names, results, instances and this will
write to files.
'''

import csv
import os
import pathlib
from pprint import pprint
from typing import Dict, Union, List, Tuple, Optional
import pyomo.environ as pyo
import pyomo.opt as opt

import runner.text as text
import runner.pyomo_runner as pyomo_runner

# TODO: Why am I returning ints? Why not just return error messages ?



# =====================================================================================
#                                   High Level Exporting Calls
# =====================================================================================


def exportRuns (outDir: str,
                runNames: List[str],
                instances: List[pyo.ConcreteModel],
                results: List[opt.SolverResults],
                outType: str,
                splitUnders: bool) -> int:
    '''
    Exports runs.
     - outType: str 'csv' or 'txt'. Tells what type of file to save each run as
     - splitUnders: if a csv, will split the variable names by underscores
            'asv_343' -> 'asv', '343 as seperate columns
     - outDir: the directory into which a new folder is created
    '''
    assert(outType == 'csv' or outType == 'txt')
    assert(len(runNames) == len(instances) == len(results))

    if outType == 'csv':
        exportManyAsCSV(
            outDir,
            runNames,
            instances,
            results,
            splitUnders
        )
    elif outType == 'txt':
        exportManyAsTXT(
            outDir,
            runNames,
            instances,
            results
        )

    print("Export success :)")


def exportSingleAsTXT (outfile, 
                    instance: pyo.ConcreteModel, 
                    result: opt.SolverResults) -> int:
    '''
    Converts a run into a single .txt file

    If verify_successful = True, it checks for the status to be 'ok'.

    Returns the number of files written (0 or 1)
    '''
    # If we're exporting to /usr/bin/dummy_out.txt
    # this expects outfile to be '/usr/bin/dummy_out'
    assert(type(outfile) == str)
    assert(str(outfile)[:-4] != '.txt')

    # With .txt files, we can export even if unsuccesfull
    # so we don't check for optimal termination

    runOut = text.exportRunText(instance, result)

    with open(outfile + ".txt", 'w') as f:
        f.write(runOut)
    
    return 1
 

def exportManyAsTXT (outfolder,
                    runNames: List[str],
                    instances: List[pyo.ConcreteModel],
                    results: List[opt.SolverResults]) -> int:
    '''
    Converts parallel lists of instances and results to file files.

    Attempts to create a folder within the specified directory

    If verify_successful = True, it checks for the status to be 'ok'.

    Returns the number of files written. -1 means error.
    '''
    return _exportMany(
        exportSingleAsTXT,
        outfolder,
        runNames,
        instances,
        results
    )


# TODO: Make split by underscore optional
def exportSingleAsCSVs (outfile, 
                    instance: pyo.ConcreteModel, 
                    result: opt.SolverResults,
                    splitUnders: bool=True) -> int:
    '''
    Converts a single run to multiple .csvs

    Expects the outfile to end in '.csv'

    If verify_successful = True, it checks for the status to be 'ok'.

    Returns the number of files written
     * -1 = error (eg: inproper file)
     * 0 = not succesfful
     * 1 = wrote file
    '''
    # Outfile is expected to be a string path to a file without an extension
    assert(type(outfile) == str)
    assert(str(outfile)[:-4] != '.csv')

    # For csv, we can only export optimal solutions
    status = result.solver.status
    if status != 'ok':
        return 0

    # Start off with variables values
    decvars_values = pyomo_runner.getVariableValues(instance)
    shadow_prices = pyomo_runner.getShadowPrices(instance)
    ge_slack = pyomo_runner.getSlackGE(instance)
    le_slack = pyomo_runner.getSlackLE(instance)


    header = []
    if splitUnders:
        # TODO: Handle different # underscores? eg: var1 = 'asd_432', var2 = 'fds_143_fds'
        #         this would require taking the max # underscores over all variables
        samplevar = list(decvars_values.keys())[0]
        num_fields = len(samplevar.split("_"))
        header = [f'tag_{n+1}' for n in range(num_fields)] + ['value']
    else:
        header = ['decision_variable', 'value']


    # Variable csv - This one we split by underscore so it's a little bit funkier
    filename = outfile + '_decision_vars.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(header)
        
        for var in decvars_values.keys():
            if splitUnders:
                writer.writerow(var.split("_") + [decvars_values[var]])
            else:
                writer.writerow([var, decvars_values[var]])
    
    # Shadow price
    _writeDictToCSV(
        outfile + "_shadow_price.csv",
        ['constraint', 'objective_value'],
        shadow_prices
    )

    # GE Slack
    _writeDictToCSV(
        outfile + "_slack_ge.csv",
        ['constraint', 'slack_ge'],
        ge_slack
    )

    # LE Slack
    _writeDictToCSV(
        outfile + "_slack_le.csv",
        ['constraint', 'slack_le'],
        le_slack
    )

    return 1


def exportManyAsCSV (outfolder,
                    runNames: List[str],
                    instances: List[pyo.ConcreteModel],
                    results: List[opt.SolverResults],
                    splitUnders=False) -> int:
    '''
    Converts parallel lists of instances and results to file files.

    Attempts to create a folder within the specified directory

    Returns the number of files written. -1 means error.
    '''
    return _exportMany(
        # Yea this is a code smell ...
        # Basically, exportMany passes 3 parameters to the exportFunction,
        # but exportCSV requires a fourth one (splitUnders), so I'm wrapping it in
        # a lambda
        lambda runPath, inst, res: exportSingleAsCSVs(runPath, inst, res, splitUnders),
        outfolder,
        runNames,
        instances,
        results,
        splitUnders
    )











# =====================================================================================
#                               Intermediate Processing Functions
# =====================================================================================

def _writeDictToCSV (filepath, header: List[str], dict: Dict[str, float]):
    '''
        Takes a 
         - header ['letter', 'value']
         - dict {'a': 43, 'b': 432}
        
        and writes a csv in the form
        letter value
        a      43
        b      432
    '''
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

        for key in dict.keys():
            writer.writerow([key, dict[key]])
    

def _exportMany (exportFunction,
                outfolder, 
                runNames: List[str],
                instances: List[pyo.ConcreteModel],
                results: List[opt.SolverResults]) -> int:
    numExport = 0

    # Step 1: Create sub directory
    if _isInvalidDir(outfolder):
        return -1

    outDir = pathlib.Path(outfolder)
    time_str = text.getTimestamp()
    subdir = f'RunOutput-{time_str}'
    outDir = outDir.joinpath(subdir)

    try:
        os.mkdir(outDir)
    except Exception:
        return -1

    # Step 2: Write to it
    for name, inst, res in zip(runNames, instances, results):
        # runNames is a list of the objective files (not their paths)
        # they should be .csv, even if we're exporting to text
        assert(name[-4:] == '.csv')
        runName = text.FILE_OUTTXT_PREFIX + name[:-4]
        runPath = str(outDir.joinpath(runName))

        succ = exportFunction(runPath, inst, res)
        if succ > 0:
            numExport += 1

    return numExport










# Util

def _isInvalidDir(dialogOutput) -> bool:
    return dialogOutput == None or type(dialogOutput) != str or dialogOutput.strip() == ""


