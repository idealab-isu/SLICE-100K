prefix = "G1 Z5 F5000\nG21\nG90 \n; Filament gcode\nM127\n;LAYER_CHANGE\n"
import os
import pdb 
from prettytable import PrettyTable
import copy
import re
import json 

def debug(layer_a, layer_b, layer_a_delimited=None, layer_b_delimited=None):
    """
    Writes the contents of the input layers to separate debug output files.

    Args:
        layer_a (str): The contents of layer A.
        layer_b (str): The contents of layer B.
        layer_a_delimited (str, optional): The delimited version of layer A. Defaults to None.
        layer_b_delimited (str, optional): The delimited version of layer B. Defaults to None.
    """
    if layer_a_delimited is not None:
        with open('debug_outputs/layer_a_delimited.gcode', 'w') as f:
            f.write(prefix + layer_a_delimited)
    if layer_b_delimited is not None:
        with open('debug_outputs/layer_b_delimited.gcode', 'w') as f:
            f.write(prefix + layer_b_delimited)
    with open('debug_outputs/layer_a.gcode', 'w') as f:
        f.write(prefix + layer_a)
    with open('debug_outputs/layer_b.gcode', 'w') as f:
        f.write(prefix + layer_b)

def convert_strings_to_table(text_1, text_2):
    """
    Display two chunks of code side-by-side in a table format.

    Args:
        text_1 (str): The first string to be converted into a table.
        text_2 (str): The second string to be converted into a table.

    Returns:
        None
    """
    # Splitting the texts by new lines to extract individual commands
    text_1_lines = text_1.strip().split('\n')
    text_2_lines = text_2.strip().split('\n')

    # Ensure both lists have equal length for a consistent table structure
    max_length = max(len(text_1_lines), len(text_2_lines))
    text_1_lines += [''] * (max_length - len(text_1_lines))
    text_2_lines += [''] * (max_length - len(text_2_lines))

    # Creating the table
    table = PrettyTable()
    table.field_names = ["Text 1", "Text 2"]

    for line1, line2 in zip(text_1_lines, text_2_lines):
        table.add_row([line1, line2])

    # Printing the table
    print(table)

def get_layers(aligned_gcode):
    layers = []
    for gcode_a,gcode_b in aligned_gcode:
        layers_a = gcode_a.split(';LAYER_CHANGE')
        layers_b = gcode_b.split(';LAYER_CHANGE')

        #add back the layer change command to each layer except first
        for i in range(1,len(layers_a)):
            layers_a[i] = ';LAYER_CHANGE' + layers_a[i]
        for i in range(1,len(layers_b)):
            layers_b[i] = ';LAYER_CHANGE' + layers_b[i]
        layers.extend(list(zip(layers_a,layers_b)))
    return layers

def chunk_debug(text_a_lines, text_b_lines, start_i, end_i, start_j, end_j, max_lines):
    """
    Debugs the chunking process by highlighting the start and end lines in the given text_a_lines and text_b_lines.

    Args:
        text_a_lines (list): List of lines from text A.
        text_b_lines (list): List of lines from text B.
        start_i (int): Start index of the chunk in text_a_lines.
        end_i (int): End index of the chunk in text_a_lines.
        start_j (int): Start index of the chunk in text_b_lines.
        end_j (int): End index of the chunk in text_b_lines.
        max_lines (int): Maximum number of lines to include in the debug output.

    Returns:
        None
    """
    if end_j == -1:
        end_j = start_j + max_lines + 1
    debug_a_lines = text_a_lines[:start_i + max_lines + 1]
    debug_b_lines = text_b_lines[:end_j + 1]

    debug_a_lines[start_i] += " START"
    debug_a_lines[end_i] += " END"

    debug_b_lines[start_j] += " START"
    debug_b_lines[end_j] += " END"

    debug_a = "\n".join(debug_a_lines)
    debug_b = "\n".join(debug_b_lines)

    debug(debug_a, debug_b)
    
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
    

