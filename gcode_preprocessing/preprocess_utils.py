prefix = "G1 Z5 F5000\nG21\nG90 \n; Filament gcode\nM127\n;LAYER_CHANGE\n"

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
