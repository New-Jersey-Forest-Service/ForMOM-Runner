'''
Export.py

This file handles all exporting. Pass in names, results, instances and this will
write to files.
'''

import csv
import os
import pathlib
from pprint import pprint
import sys
from typing import Dict, Union, List, Tuple, Optional
import pyomo.environ as pyo
import pyomo.opt as opt

import runner.csv_to_dat as converter
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
    assert(pathlib.Path(outDir).exists())
    assert(pathlib.Path(outDir).is_dir())

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


def exportSummaryTXT (outfile,
                    runNames: List[str],
                    instances: List[pyo.ConcreteModel],
                    results: List[opt.SolverResults]):
    '''
    Generates a .txt file with descriptions of all runs in aggregate
    '''
    assert(type(outfile) == str)
    assert(outfile[:-4] != '.txt')
    summaryText = text.exportSummaryText(runNames, instances, results)

    with open(outfile + '.txt', 'w') as f:
        f.write(summaryText)


def exportSummaryCSV (outfile,
                    runNames: List[str],
                    instances: List[pyo.ConcreteModel],
                    results: List[opt.SolverResults]):
    '''
    Generates a .csv file with summary statistics for all runs
    '''
    assert(type(outfile) == str)
    assert(outfile[:-4] != '.csv')

    all_runs_info = []
    for inst, res in zip(instances, results):
        all_runs_info.append(pyomo_runner.getRunSummary(inst, res))
    
    fields = ['name'] + list(all_runs_info[0].keys())

    with open(outfile + '.csv', 'w') as f:
        w = csv.DictWriter(f, fields)

        w.writeheader()
        for name, info in zip(runNames, all_runs_info):
            w.writerow({'name': name, **info})


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
 

def exportManyAsTXT (outFolder,
                    runNames: List[str],
                    instances: List[pyo.ConcreteModel],
                    results: List[opt.SolverResults]) -> int:
    '''
    Converts parallel lists of instances and results to file files.

    Attempts to create a folder within the specified directory

    If verify_successful = True, it checks for the status to be 'ok'.

    Returns the number of files written. -1 means error.
    '''
    nWritten = _exportManyRuns(
        exportSingleAsTXT,
        exportSummaryTXT,
        outFolder,
        runNames,
        instances,
        results
    )

    return nWritten


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


def exportManyAsCSV (outFolder,
                    runNames: List[str],
                    instances: List[pyo.ConcreteModel],
                    results: List[opt.SolverResults],
                    splitUnders=False) -> int:
    '''
    Converts parallel lists of instances and results to file files.

    Attempts to create a folder within the specified directory

    Returns the number of files written. -1 means error.
    '''
    return _exportManyRuns(
        # Yea this is a code smell ...
        # Basically, exportMany passes 3 parameters to the exportFunction,
        # but exportCSV requires a fourth one (splitUnders), so I'm wrapping it in
        # a lambda
        lambda runPath, inst, res: exportSingleAsCSVs(runPath, inst, res, splitUnders),
        exportSummaryCSV,
        outFolder,
        runNames,
        instances,
        results
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
    

def _exportManyRuns (funcExportRun,
                funcExportSummary,
                outFolder, 
                runNames: List[str],
                instances: List[pyo.ConcreteModel],
                results: List[opt.SolverResults]) -> int:
    numExport = 0

    # Step 1: Create sub directory
    if _isInvalidDir(outFolder):
        return -1

    outDir = pathlib.Path(outFolder)
    time_str = text.getTimestamp()
    subdir = f'RunOutput-{time_str}'
    outDir = outDir.joinpath(subdir)

    try:
        os.mkdir(outDir)
    except Exception:
        return -1

    # Step 2: Write to it
    summaryFile = str(outDir.joinpath('SUMMARY'))
    funcExportSummary(summaryFile, runNames, instances, results)

    for name, inst, res in zip(runNames, instances, results):
        # runNames is a list of the objective files (not their paths)
        # they should be .csv, even if we're exporting to text
        assert(name[-4:] == '.csv')
        runName = text.FILE_OUTTXT_PREFIX + name[:-4]
        runPath = str(outDir.joinpath(runName))

        succ = funcExportRun(runPath, inst, res)
        print(f"Exported?: {succ}")
        if succ > 0:
            numExport += 1

    return numExport










# Util

def _isInvalidDir(dialogOutput) -> bool:
    return dialogOutput == None or type(dialogOutput) != str or dialogOutput.strip() == ""







# Run the file to output sample data into a directory
if __name__ == '__main__':
    # Filepaths (change to your machine)
    file_constraint = '/home/velcro/Documents/Professional/NJDEP/TechWork/ForMOM-Runner/sample-data/icecream_const.csv'
    file_objective = '/home/velcro/Documents/Professional/NJDEP/TechWork/ForMOM-Runner/sample-data/icecream_obj.csv'
    OUTPUT_DIR = './'

    # Reading files
    objData, constrData, err = converter.lintInputDataFromFilepaths(file_objective, file_constraint)
    if objData == None:
        print("Error loading sample data :/")
        print(err)
        sys.exit(1)

    finalModel = converter.convertInputToFinalModel(objData, constrData)

    # Run the model
    datadict = converter.convertFinalModelToDataDict(finalModel)
    inst = pyomo_runner.loadPyomoModelFromDataDict(datadict)
    inst, res = pyomo_runner.solveConcreteModel(inst, verboseToConsole=True)

    # Export
    objFileName = pathlib.Path(file_objective).parts[-1]

    exportRuns(
        OUTPUT_DIR,
        [objFileName],
        [inst],
        [res],
        'csv',
        True
    )

    print(pyomo_runner.getRunSummary(inst, res))

    print("Finished")


