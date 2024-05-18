import pdb
import re
import matplotlib.pyplot as plt
import numpy as np

def parse_gcode(gcode):
    layer_dict = {}
    current_z = None  # Initialize current_z to a default value
    last_x, last_y = None, None  # Track the last position
    skip = True  # Start with skipping until 'Skirt/Brim' is found
    is_extruding = False  # Track whether the current move involves extrusion
    
    for line in gcode.split('\n'):
        if ';TYPE:Skirt/Brim' in line:
            skip = False
        if ';TYPE:Perimeter' in line or ';TYPE:External perimeter' in line:
            skip = False

        if not skip and line.startswith('G1'):
            # Reset extrusion status on non-extrusion lines
            if 'E' not in line:
                is_extruding = False

            # Check for X, Y, Z coordinates
            x_match = re.search(r'X([0-9]+\.?[0-9]*)', line)
            y_match = re.search(r'Y([0-9]+\.?[0-9]*)', line)
            z_match = re.search(r'Z([0-9]+\.?[0-9]*)', line)

            x = float(x_match.group(1)) if x_match else last_x
            y = float(y_match.group(1)) if y_match else last_y
            if z_match:
                current_z = float(z_match.group(1))

            # Determine if this line involves extrusion
            if 'E' in line:
                is_extruding = True

            # Store the position if this is an extrusion move or first move on this layer
            if is_extruding and x is not None and y is not None:
                if current_z not in layer_dict:
                    if current_z is None:
                        # use regex to find the Z value (e.g Z:0.65 should be 0.65)
                        try:
                            current_z = float(re.search(r'Z:([0-9]+\.?[0-9]*)', gcode).group(1))
                        except:
                            pdb.set_trace()
                    layer_dict[current_z] = []
                if last_x is not None and last_y is not None:  # Avoid adding the very first uninitialized point
                    layer_dict[current_z].append((last_x, last_y, x, y))

            # Update last known positions
            last_x, last_y = x, y

    return layer_dict

def plot_layer(layer_dict,render_path, layer_num=None):
    layer_num = int(layer_num)
    if None in layer_dict:
        layer_dict[-1] = layer_dict[None]
        del layer_dict[None]

    plt.figure(figsize=(10, 8))
    if layer_num is None:
        layers = layer_dict.keys()
    else:
        sorted_keys = sorted(layer_dict.keys())
        layers = [sorted_keys[layer_num]]
        
    for z in layers:
        points = layer_dict.get(z, [])
        for (x1, y1, x2, y2) in points:
            plt.plot([x1, x2], [y1, y2], color='blue', linewidth=0.35)
            # plt.plot([x1, x2], [y1, y2], label=f'Layer {z}' if len(layer_dict) == 1 else "")

    plt.title(f'G-code Layer Visualization - Layer {layer_num}' if layer_num else 'All Layers')
    plt.savefig(render_path)
    
    img = plt.imread(render_path)
    #load image back as binary array and convert to numpy array
    img = np.array(img)
    return img [:,:,0]

if __name__ == "__main__":
    # Assuming 'gcode_path' is the path to your G-code file
    gcode_path = "/vast/km3888/paired_gcode/thingiverse_10k_marlin/thing-10057-file-32149_objaverse_xl_config_marlin.gcode"
    #load gcode from gcode_path
    gcode = open(gcode_path, 'r').read()
    gcode_layers = parse_gcode(gcode)

    # Visualize the layers
    lyr_input = input("Enter the layer number to visualize: ")

    while lyr_input != "exit":
        plot_layer(gcode_layers, float(lyr_input))
        lyr_input = input("Enter the layer number to visualize: ")

    # plot_layer(gcode_layers, 2.45)
