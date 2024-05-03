prefix = "G1 Z5 F5000\nG21\nG90 \n; Filament gcode\nM127\n;LAYER_CHANGE\n"
import os
import pdb 
from prettytable import PrettyTable
import copy
import re

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
    

def relative_extrusion(layer):
    """
    Converts absolute extrusion values in a G-code layer to relative extrusion values.

    Each line of G-Code specifies extrusion at a given position. The extrusion values are absolute,
    meaning they represent the total amount of filament extruded up to that point. 
    What really matters though is the relativate extrusion value, how much new material is being
    created at that location (since we'll be changing the ordering when we do contour flipping). 
    
    Args:
        layer (str): The G-code layer to process.

    Returns:
        str: The processed G-code layer with relative extrusion values.

    Raises:
        AssertionError: If any of the relative extrusion values are not greater than zero.
    """
    inks = layer.split('G92 E0')
    relative_inks = [inks[0]]
    for ink in inks[1:]:
        marked_lines = []
        initialized = False
        # demarkate all the relevant extrusion values in this ink
        for line in ink.split('\n'):
            #not sure whether lines including F should be included,
            #I'll look at more examples:
            if 'G1' in line and 'E' in line and (not 'F' in line or not initialized):
                if 'F' in line:
                    initialized = True
                # convert line to array of characters
                line_chars = list(line)
                # find the index of the character 'E'
                e_index = line_chars.index('E')
                # find the index of the last consecutive digit following E
                # e.g for E1922.293, the index of the last digit is 8
                last_digit_index = e_index + 1
                while last_digit_index < len(line) and (line[last_digit_index].isdigit() or line[last_digit_index] == '.'):
                    last_digit_index += 1
                # replace E[number] with E<e>[number]<e>
                marked_line_chars = copy.deepcopy(line_chars)
                marked_line_chars.insert(e_index+1, '<e>')
                marked_line_chars.insert(last_digit_index + 1, '<e>')
                # convert the array back to a string
                marked_line = ''.join(marked_line_chars)
                marked_lines.append(marked_line)
            else:
                marked_lines.append(line)
        marked_ink = '\n'.join(marked_lines)
        # now all the numbers n_1,n_2,...,n_k are marked with <e> around them
        # what we want to do now is replace n_i with n_i - n_{i-1} for i>1 and n_1 with n_1

        # find all the marked numbers
        numbers = re.findall(r'<e>[0-9]*\.?[0-9]*<e>', marked_ink)
        if not len(numbers):
            relative_inks.append(ink)
            continue
        # remove the <e> tags
        numbers = [number[3:-3] for number in numbers]
        # convert the numbers to floats
        float_numbers = [float(number) for number in numbers]
        # compute the relative extrusion
        relative_numbers = [float_numbers[0]] + [float_numbers[i] - float_numbers[i-1] for i in range(1, len(float_numbers))]
        # replace the marked numbers with the relative extrusion
        assert all([x>0 for x in relative_numbers])
        relative_numbers_w_e = ["<e>" + str(number) + "<e>" for number in float_numbers]
        relative_ink = marked_ink
        for i in range(len(numbers)):
            str_num = str(relative_numbers[i])
            if "e" in str_num:
                str_num = "{:f}".format(float(str_num))
            replace_val = f'<e>{str_num}<e>'
            if not all([x.isdigit() or x=="." for x in str_num]):
                pdb.set_trace()
            relative_ink = relative_ink.replace(f'<e>{numbers[i]}<e>', replace_val)
            # print(f'<e>{numbers[i]}<e> -> {replace_val}')
        relative_inks.append(relative_ink)
    relative_layer = 'G92 E0'.join(relative_inks)
    # save both of the layers to a .gcode file using debug()
    debug(layer, relative_layer)
    return relative_layer

def absolute_extrusion(layer):
    """
    Converts a layer with relative extrusion values to absolute extrusion values.

    Args:
        layer (str): The layer with relative extrusion values.

    Returns:
        str: The layer with absolute extrusion values.
    """
    # Recover original layer from relative extrusion
    relative_inks = layer.split('G92 E0')
    absolute_inks = [relative_inks[0]]
    for ink in relative_inks[1:]:
        # get all the string portions surrounded by <e> tags
        relative_values = re.findall(r'<e>[0-9]*\.?[0-9]*<e>', ink)
        if len(relative_values) == 0:
            absolute_inks.append(ink)
            continue
        # remove the <e> tags
        relative_values_nums = [value[3:-3] for value in relative_values]
        absolute_values = [float(relative_values_nums[0])]
        for i in range(1, len(relative_values_nums)):
            new_abs_val = absolute_values[-1] + float(relative_values_nums[i])
            if len(str(new_abs_val).split('.')[1])>5:
                old_abs_val = new_abs_val
                new_abs_val_str = str(new_abs_val)

                # check if value should be rounded up or down
                if new_abs_val_str.split('.')[1][5] >= '5':
                    new_abs_val = str(round(new_abs_val, 5))
                else:
                    new_abs_val = str(round(new_abs_val- 0.00001, 5))
                new_abs_val = float(new_abs_val)
                pdb.set_trace()
            absolute_values.append(new_abs_val)
        
        if (absolute_values[0] - int(absolute_values[0]) == 0):
            absolute_values[0] = int(absolute_values[0])

        if any([float(x) < 0 for x in relative_values_nums]):
            print("Negative value found in relative extrusion")
        # replace the relative values with the absolute values
        for i in range(len(relative_values)):
            #old code: this replaces all instances of the relative value with the absolute value
            # ink = ink.replace(relative_values[i], str(absolute_values[i]))
            #new code: this replaces only the first instance of the relative value with the absolute value
            if not all([x.isdigit() or x == '.' for x in str(absolute_values[i])]):
                print(f"Relative value {relative_values[i]} is not a number")
                pdb.set_trace()
            str_abs = str(absolute_values[i])
            
            ink = ink.replace(relative_values[i], str(absolute_values[i]), 1)
        
        if "<e>" in ink:
            pdb.set_trace()
        absolute_inks.append(ink)

    absolute_layer = 'G92 E0'.join(absolute_inks)
    return absolute_layer

def test_extrusion(args):
    data = get_data(args.data_path,1)
    layers = get_layers(data)
    for layer_a,layer_b in layers[1:]:
        processed = relative_extrusion(layer_a)
        unprocessed = absolute_extrusion(processed)
        length=2500
        convert_strings_to_table(layer_a[1900:length],unprocessed[1900:length])
        if layer_a != unprocessed:
            print('Error in relative extrusion')
            pdb.set_trace()