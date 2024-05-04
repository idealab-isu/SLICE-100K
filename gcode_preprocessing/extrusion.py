from preprocess_utils import debug, get_layers, make_json, \
                                get_data, \
                                convert_strings_to_table
import pdb
import re
import copy

def sailfish_relative_extrusion(layer,init_val=None):
    demarcated_layer = demarcate_extrusion_vals(layer, get_initial=False)
    resets = re.finditer(r'G1 E([0-9\.]+) F([0-9]+)', demarcated_layer)
    resets = [match for match in resets]
    reset_indices = [match.start() for match in resets]

    #get indices of all numbers between <e> tags
    numbers = re.finditer(r'<e>[0-9]*\.?[0-9]*<e>', demarcated_layer)
    numbers = [match for match in numbers]
    number_indices = [match.start() for match in numbers]

    with_initial = []
    relative_inks = []
    number_i = 0
    # for each reset_i, find the list of number indices n_i such that 
    # reset_i is the last reset index that comes before it

    for i in range(len(reset_indices)):
        reset_i = reset_indices[i]
        # find the list of number indices n_i such that reset_i is the last reset index that comes before it
        following_nums = []
        while number_i < len(number_indices) and number_indices[number_i] < reset_i:
            following_nums.append(numbers[number_i])
            number_i += 1
        if i==0:
            if len(following_nums)>0:
                assert init_val is not None
                with_initial.append((init_val, following_nums))
            else:
                relative_inks.append(demarcated_layer[:reset_i])
        else:
            with_initial.append((resets[i-1], following_nums))
    with_initial.append((resets[-1], numbers[number_i:]))
    
    for i in range(len(with_initial)):
        # these are basically their own "inks"
        if i==0 and len(relative_inks)==0:
            init_val, number_matches = with_initial[i]
            relative_ink = demarcated_layer[:with_initial[i+1][0].start()]
        else:
            reset, number_matches = with_initial[i]
            init_val = float(reset.group(1))
            # take substring of layer from this reset to the next reset
            # this is what we're going to augment and added to relative_inks
            if i == len(with_initial)-1:
                relative_ink = demarcated_layer[reset.start():]
            else:
                next_reset = with_initial[i+1][0]
                relative_ink = demarcated_layer[reset.start():next_reset.start()]

        
        numbers = [match.group(0) for match in number_matches]
        if not len(numbers):
            relative_inks.append(relative_ink)
            continue
        # remove the <e> tags
        numbers_stripped = [number[3:-3] for number in numbers]
        # convert the numbers to floats
        float_numbers = [float(number) for number in numbers_stripped]
        # compute the relative extrusion
        relatives = [float_numbers[0]-init_val]
        for i in range(1, len(float_numbers)):
            relatives.append(float_numbers[i] - float_numbers[i-1])
        # replace the marked numbers with the relative extrusion
        assert all([x>0 for x in relatives])


        for i in range(len(numbers)):
            str_num = str(relatives[i])
            if "e" in str_num:
                str_num = "{:f}".format(float(str_num))
            replace_val = f'<e>{str_num}<e>'
            if not all([x.isdigit() or x=="." for x in str_num]):
                pdb.set_trace()

            relative_ink = relative_ink.replace(f'{numbers[i]}', replace_val)

        relative_inks.append(relative_ink)
    relative_layer = ''.join(relative_inks)
    next_init_val = float(with_initial[-1][0].group(1))
    return relative_layer,next_init_val

def sailfish_absolute_extrusion(layer,init_val=None):
    resets = re.finditer(r'G1 E([0-9\.]+) F([0-9]+)', layer)
    resets = [match for match in resets]
    reset_indices = [match.start() for match in resets]

    #get indices of all numbers between <e> tags
    numbers = re.finditer(r'<e>[0-9]*\.?[0-9]*<e>', layer)
    numbers = [match for match in numbers]
    number_indices = [match.start() for match in numbers]

    with_initial = []
    absolute_inks = []
    number_i = 0
    # for each reset_i, find the list of number indices n_i such that 
    # reset_i is the last reset index that comes before it
    for i in range(len(reset_indices)):
        reset_i = reset_indices[i]
        # find the list of number indices n_i such that reset_i is the last reset index that comes before it
        following_nums = []
        while number_i < len(number_indices) and number_indices[number_i] < reset_i:
            following_nums.append(numbers[number_i])
            number_i += 1
        if i==0:
            if len(following_nums)>0:
                assert init_val is not None
                with_initial.append((init_val, following_nums))
            else:
                absolute_inks.append(layer[:reset_i])
        else:
            with_initial.append((resets[i-1], following_nums))
    with_initial.append((resets[-1], numbers[number_i:]))

    for i in range(len(with_initial)):
        init = with_initial[i][0]

        # get the portion of layer from the reset to the next reset
        # if i == len(with_initial)-1:
        #     absolute_ink = layer[init.start():]
        # else:
        #     next_reset = with_initial[i+1][0]
        #     absolute_ink = layer[init.start():next_reset.start()]
        
        #####
        if i==0 and len(absolute_inks)==0:
            init_val, number_matches = with_initial[i]
            absolute_ink = layer[:with_initial[i+1][0].start()]
        else:
            reset, number_matches = with_initial[i]
            init_val = float(reset.group(1))
            # take substring of layer from this reset to the next reset
            # this is what we're going to augment and added to relative_inks
            if i == len(with_initial)-1:
                absolute_ink = layer[init.start():]
            else:
                next_reset = with_initial[i+1][0]
                absolute_ink =layer[init.start():next_reset.start()]
        #####

        numbers = [match.group(0) for match in with_initial[i][1]]
        if not len(numbers):
            if "<e>" in absolute_ink:
                pdb.set_trace()
            absolute_inks.append(absolute_ink)
            continue
        # remove the <e> tags
        numbers_stripped = [number[3:-3] for number in numbers]
        # convert the numbers to floats
        float_numbers = [float(number) for number in numbers_stripped]
        # compute the absolute extrusion
        absolutes = [init_val + float_numbers[0]]
        for i in range(1, len(float_numbers)):
            new_abs_val = absolutes[-1] + float_numbers[i]
            if len(str(new_abs_val).split('.')[1])>5:
                old_abs_val = new_abs_val
                new_abs_val_str = str(new_abs_val)

                # check if value should be rounded up or down
                if new_abs_val_str.split('.')[1][5] >= '5':
                    new_abs_val = str(round(new_abs_val, 5))
                else:
                    new_abs_val = str(round(new_abs_val- 0.00001, 5))
                new_abs_val = float(new_abs_val)
            absolutes.append(new_abs_val)
            # replace the marked numbers with the absolute extrusion
        assert min(absolutes) > 0
        for i in range(len(numbers)):
            if not all([x.isdigit() or x == '.' for x in str(absolutes[i])]):
                print(f"Relative value {relative_values[i]} is not a number")
                pdb.set_trace()
            str_abs = str(absolutes[i])
            
            absolute_ink = absolute_ink.replace(numbers[i], str(absolutes[i]), 1)
        
        if "<e>" in absolute_ink:
            pdb.set_trace()
        absolute_inks.append(absolute_ink)
    absolute_layer = ''.join(absolute_inks)
    absolute_layer = absolute_layer.replace('E0.', 'E.')
    if '<e>' in absolute_layer:
        pdb.set_trace()
    next_init_val = float(with_initial[-1][0].group(1))
    return absolute_layer,next_init_val


def demarcate_extrusion_vals(gcode, get_initial=True):
    marked_lines = []
    initialized = not get_initial
    # demarkate all the relevant extrusion values in this ink
    for line in gcode.split('\n'):
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
    return marked_ink

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
    if 'G92 E0' not in layer:
        layer = sailfish_relative_extrusion(layer)
    inks = layer.split('G92 E0')
    relative_inks = [inks[0]]
    for ink in inks[1:]:
        marked_ink = demarcate_extrusion_vals(ink)
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
    if 'G92 E0' not in layer:
        layer = sailfish_absolute_extrusion(layer)
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
    return absolute_layer, None

def test_extrusion(args):
    data = get_data(args.data_path,1)
    layers = get_layers(data)
    init_val = None
    for layer_a,layer_b in layers[1:]:
        processed,_ = sailfish_relative_extrusion(layer_b,init_val)
        unprocessed,init_val = sailfish_absolute_extrusion(processed,init_val)
        length=175
        convert_strings_to_table(layer_b[:length],unprocessed[:length])
        layer_b[:165] == unprocessed[:165]
        if layer_b != unprocessed:
            print('Error in relative extrusion')
            for i in range(len(layer_b)):
                if layer_b[i] != unprocessed[i]:
                    print(f'Error at index {i}') 
                    break
            pdb.set_trace() #there's one layer where it hits this breakpoint but it's just a small rounding error