# ForMOM Runner
*GUI Application*

**TODO: Insert Picture**

This program takes two .csv files specifying a linear optimization problem,
presumably built with the ForMOM Model Builder, and runs the model.

Outputs include
 - values of decision variables
 - constraint slacks - how much of the constraint's values are unused
 - constraint shadow prices - how much bang for your buck do you get from relaxing the constraints

**Credits**: The original csv format was made by Bill, and the converter was written by both Michael and Bill


## Running

Python module requirements are in the requirements.txt file. Linear optimization is
done with Pyomo which may require a system-level installation for the solver.
Check out the [Pyomo Installation Guide](http://www.pyomo.org/installation) for
help.

The file to run is launchgui.py.

For more info checkout the [ForMOM Wiki](https://github.com/New-Jersey-Forest-Service/ForMOM/wiki).
