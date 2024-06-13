import os
import random
from joblib import Parallel, delayed
import time
import sys
import json
import subprocess
import cProfile
from tqdm import tqdm
import pstats


def slice_file(prusa_path, config_path, stl_file, output_file):

    slicing_command = [prusa_path, "-g", "--info", stl_file, "--load", config_path, "-o", output_file]
    
    result_slicing = subprocess.run(slicing_command, text=True, capture_output=True) # use for python version > 3.7

    if result_slicing.returncode == 0:
        output = result_slicing.stdout
    else:
        error_message = f"Error running PrusaSlicer: {result_slicing.stderr}"
        return stl_file, error_message, None

    return None, None, output


def slice_single_file(input_dir, prusa_path, config_dir, config_names, stl_file, output_dir):

    config_name = random.choice(config_names)
    print('config_name: ', config_name)
    config_path = os.path.join(config_dir, config_name)
    print('config_path: ', config_path)
    output_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(stl_file))[0]}_{os.path.splitext(config_name)[0]}.bgcode")
    print('output_file: ', output_file)
    stl_path = os.path.join(input_dir, stl_file)
    print('stl_path: ', stl_path)

    # slice file    
    stl_error, error_message, output = slice_file(prusa_path, config_path, stl_path, output_file)

    # Handle errors and outputs
    if stl_error is not None:
        error_details = f"Error in file {stl_error}: {error_message}\n"  # Formatting as a string
        sys.stderr.write(error_details) 
    else:
        print(f"File {stl_file} sliced successfully. Output: {output}")

if __name__ == "__main__":

    input_dir = sys.argv[1]
    prusa_path = sys.argv[2]
    config_dir = sys.argv[3]
    config_names = sys.argv[4].split(',')
    stl_file = sys.argv[5]
    output_dir = sys.argv[6]
    slice_single_file(input_dir, prusa_path, config_dir, config_names, stl_file, output_dir)


    ###### FOR DEBUGGING ######

    # input_dir = "path to stl directory"
    # output_dir = "path to directory where gcode will be saved"
    # prusa_path = "path to your PrusaSlicer executable"
    # config_names = ["objaverse_xl_config_1.ini", "objaverse_xl_config_2.ini", "objaverse_xl_config_3.ini", "objaverse_xl_config_4.ini"]
    # config_dir = "path to config directory"
    # stl_file = "name of stl file to be sliced"
    
    # slice_single_file(input_dir, prusa_path, config_dir, config_names, stl_file, output_dir)
