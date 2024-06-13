# Slicing STL Files

All the code for slicing STL files and storing them in .bgcode format.


## Installation

Create a new environment and run:

```conda env create -f llm.yml```


Install a PrusaSlicer version compatible with your system from here -

https://github.com/prusa3d/PrusaSlicer/releases

We used version 2.7.1 for our experiments on a Linux machine.

For converting .bgcode files to .gcode files and vice-versa, we used the following repository:

https://github.com/prusa3d/libbgcode/blob/main/doc/building.md

Go ahead and build it from source.

For conversion we use the following commands:
    
    ```pathToBgcodeExecutable pathTo.bgcodeFile```

For more information we recommend looking at this - 

https://github.com/prusa3d/libbgcode/blob/main/doc/bgcode.md

## Running

We provide an example slurm script to run the slicing on a cluster. __config_files__ folder contains four different config files we used. You can run it with:

```sbatch example_slice.txt```

Internally, it calls __slice_binary_gcode.py__. Make sure to edit the paths in the script to match your system paths.

Furthermore, __slice_binary_gcode.py__ can be used for debugging purposes by uncommenting the debugging section and issuing:
    
```python slice_binary_gcode.py```

