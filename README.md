# ForMOM Runner
*GUI Application*

![22Week_ModelRunner](https://user-images.githubusercontent.com/49537988/181365320-7868a2d1-0cb4-4ce9-b08d-bef3a5cf4b70.png)

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

The file to run is \_\_main__.py, located in src.

Additionally, the software can be run from the main [ForMOM repo](https://github.com/New-Jersey-Forest-Service/ForMOM)
by executing the .pyz file located in the [software folder](https://github.com/New-Jersey-Forest-Service/ForMOM/tree/main/software).

For more info checkout the [ForMOM Wiki](https://github.com/New-Jersey-Forest-Service/ForMOM/wiki).
