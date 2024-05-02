from tqdm import tqdm
import json
from prettytable import PrettyTable
from transformers import AutoTokenizer
import pdb
import os
import sys
import argparse

from preprocess_utils import debug
from chunking import aligned_chunks
from contour_flipping import flip_on_contours

access_token = "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"

def make_json(chunk_list):
    """
    Converts a list of chunks into a JSON file.

    Parameters:
    - chunk_list (list): A list of dictionaries representing chunks.

    Returns:
    - None

    Example Usage:
    >>> chunks = [
    ...     {"text_1": "G1 X10 Y20", "text_2": "G1 X20 Y30"},
    ...     {"text_1": "G1 Z10", "text_2": "G1 Z20"}
    ... ]
    >>> make_json(chunks)

    This function takes a list of chunks, where each chunk is a dictionary with two keys: "text_1" and "text_2".
    It creates a new dictionary for each chunk, with a "text" key that contains a formatted string representing the chunk.
    The formatted string includes the input and output texts from the chunk.
    Finally, it writes the list of dictionaries to a JSON file.

    Note: The JSON file path is hardcoded in the function and may need to be modified to match your desired location.
    """
    out_list = []
    for chunk in chunk_list:
        a = chunk["text_1"]
        b = chunk["text_2"]
        out_dict = {}
        out_dict['text'] = f"Instruction: Translate the inputted GCode from Marlin to Sailfish \n Input:{a} \n Output:{b}" 
        out_list.append(out_dict)
    json.dump(out_list, open(f"/vast/km3888/paired_gcode/test_aligned_chunks_{args.n_files}_{args.chunk_size}.json", 'w'))
    
def get_data(data_path, n_files):
    """
    Retrieve the content of G-code files from two directories and return a list of tuples containing the extracted content.

    Args:
        data_path (str): The path to the directory containing the G-code files.
        n_files (int): The number of files to process from the directory.

    Returns:
        list: A list of tuples, where each tuple contains the extracted content from two corresponding G-code files.

    """
    gcode_path_a = os.path.join(data_path, "thingiverse_10k_marlin")
    gcode_path_b = os.path.join(data_path, "thingiverse_10k_sailfish")
    
    output = []
    for i, file_name_a in enumerate(os.listdir(gcode_path_a)[:n_files]):
        path_a = os.path.join(gcode_path_a, file_name_a)
        path_b = path_a.replace('marlin', 'sailfish')
        if not os.path.exists(path_b):
            print(f'{path_b} does not exist')
            continue

        file_a = open(path_a, 'r').read()
        file_b = open(path_b, 'r').read()

        debug_marlin = '\n'.join(file_a.split('\n')[:500])
        with open('og_marlin.gcode', 'w') as f:
            f.write(debug_marlin)

        content_a = file_a.split('G28')[1]
        content_b = file_b.split('G28')[1]
        
        output.append((content_a, content_b))
    return output

def main(args):
    """
    Main function for aligning and processing G-code files.

    Saves G-code chunks in a JSON file to be used for training the model.

    Args:
        args: Command-line arguments passed to the script.

    Returns:
        None
    """
    
    data = get_data(args.data_path,args.n_files)
    # Re-arrange Marlin G-code so that the ordering of the contours 
    # is the same as in the Sailfish version
    aligned_gcode = []
    total_successes = 0
    total_failures = 0
    print('Performing contour flipping on %s files' % args.n_files)
    for i in tqdm(range(len(data))):
        gcode_a, gcode_b = data[i]
        flipped_a,flipped_b,successes,failures = flip_on_contours(gcode_a,gcode_b)
        aligned_gcode.append((flipped_a,flipped_b))
        total_successes+=successes
        total_failures+=failures
    print('finished contour flipping!')
    print(f'{total_successes}/{total_successes+total_failures} layers successfully aligned')

    # Split up Marlin and Sailfish into corresponding chunks that are small enough
    # to fit in context window of transformer-based model
    chunk_list = []
    successes = 0
    failures = 0
    print('Creating chunks from %s files' % len(aligned_gcode))
    for i in tqdm(range(len(aligned_gcode))):
        aligned_a,aligned_b = aligned_gcode[i]
        try:
            chunks = aligned_chunks(aligned_a,aligned_b,args.chunk_size)
            chunk_list.extend(chunks)
        except:
            failures+=1
    print(f'{successes}/{successes+failures} files successfully chunked')

    make_json(chunk_list)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_files", type=int, default=200)
    parser.add_argument("--chunk_size", type=int, default=15)
    parser.add_argument("--data_path", type=str, default="/vast/km3888/paired_gcode")
    parser.add_argument("--output_path", type=str, default="/vast/km3888/paired_gcode/chunked_data")
    args = parser.parse_args()

    main(args)