# Generating Blender Renders of STL Files

All the scripts for making blender renderings of STL files. We largely follow Objaverse-XL's blender rendering script (https://github.com/allenai/objaverse-xl/tree/main/scripts/rendering)


## Installation

Create a new environment and run:

```conda env create -f blender.yml```


Download the blender executable as described here - 

https://github.com/allenai/objaverse-xl/tree/main/scripts/rendering

Then edit the following paths - 
line 149: command = f"ADD YOUR PATH HERE -b --python blender_script.py -- {args}"

line 351: return pd.read_json("ADD_PATH_YOUR_PATH/file_list.json", orient="records")

line 440: data_dir = "ADD_YOUR_PATH_TO_STL_FILES_HERE"

line 441: save_dir = "ADD_YOUR_PATH_TO_SAVE_RENDERS_HERE"


__file_list.json__ contains filenames to render. It was introduced as a way to render large datasets in batches.

## Running
We provide a slurm script to run the blender rendering script on a cluster. To run the script, use the following command:

```sbatch slurm_batch.txt```

Make sure to edit the slurm script to include the correct config parameters, paths to the blender executable, conda environment, and the python script.

Internally, custom_main.py calls blender_script.py

