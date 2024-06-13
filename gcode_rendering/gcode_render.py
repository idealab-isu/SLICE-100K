import re
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def parse_gcode(gcode_file):
    layer_dict = {}
    current_z = None
    last_x, last_y = None, None
    skip = True
    is_extruding = False

    with open(gcode_file, 'r') as file:
        for line in file:
            if ';TYPE:Skirt/Brim' in line:
                skip = False
            if ';TYPE:Perimeter' in line or ';TYPE:External perimeter' in line:
                skip = False

            if not skip and line.startswith('G1'):
                if 'E' not in line:
                    is_extruding = False
                x_match = re.search(r'X([0-9]+\.?[0-9]*)', line)
                y_match = re.search(r'Y([0-9]+\.?[0-9]*)', line)
                z_match = re.search(r'Z([0-9]+\.?[0-9]*)', line)

                x = float(x_match.group(1)) if x_match else last_x
                y = float(y_match.group(1)) if y_match else last_y
                if z_match:
                    current_z = float(z_match.group(1))

                if 'E' in line:
                    is_extruding = True

                if is_extruding and x is not None and y is not None:
                    if current_z not in layer_dict:
                        layer_dict[current_z] = []
                    if last_x is not None and last_y is not None:
                        layer_dict[current_z].append((last_x, last_y, x, y))

                last_x, last_y = x, y

    return layer_dict

def distance_and_angle(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    distance = np.sqrt(dx ** 2 + dy ** 2)
    angle = np.degrees(np.arctan2(dy, dx))
    return distance, angle

def plot_layer(layer_dict, bbox, width, layer_num=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    if layer_num is None:
        layers = layer_dict.keys()
    else:
        layers = [layer_num]
    
    for z in layers:
        points = layer_dict.get(z, [])
        for (x1, y1, x2, y2) in points:
            length, angle = distance_and_angle(x1, y1, x2, y2)
            rect = patches.Rectangle((x1, y1 - 0.175), length, width, angle=angle,
                                     edgecolor='none', facecolor='k', alpha=0.5)
            ax.add_patch(rect)

    plt.title(f'G-code Layer Visualization - Layer {layer_num}' if layer_num else 'All Layers')
    # if len(layer_dict) == 1:
        # plt.legend()
    # plt.grid(True)
    ax.set_xlim(0.9*bbox[0], 1.1*bbox[1])
    ax.set_ylim(0.9*bbox[2], 1.1*bbox[3])
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.show()


gcode_path = "path to .gcode file"
width = 0.3
gcode_layers = parse_gcode(gcode_path)
total_keys = len(gcode_layers.keys())

gcode_layers = dict(zip(range(total_keys), gcode_layers.values()))

x_vals = []
y_vals = []
for z, points in gcode_layers.items():
    for (x1, y1, x2, y2) in points:
        x_vals.extend([x1, x2])
        y_vals.extend([y1, y2])

bbox = (min(x_vals), max(x_vals), min(y_vals), max(y_vals))
print(f"Bounding box: {bbox}")

lyr_input = input("Enter the layer number to visualize: ")

while lyr_input != "exit":
    plot_layer(gcode_layers, bbox, width, float(lyr_input))
    lyr_input = input("Enter the layer number to visualize: ")
