prefix = "G1 Z5 F5000\nG21\nG90 \n; Filament gcode\nM127\n;LAYER_CHANGE\n"

def debug(layer_a,layer_b,layer_a_delimited=None,layer_b_delimited=None):
    # save all of layer_a and layer_b along with their delimited counterparts
    if layer_a_delimited is not None:
        with open('debug_outputs/layer_a_delimited.gcode','w') as f:
            f.write(prefix+layer_a_delimited)
    if layer_b_delimited is not None:
        with open('debug_outputs/layer_b_delimited.gcode','w') as f:
            f.write(prefix+layer_b_delimited)
    with open('debug_outputs/layer_a.gcode','w') as f:
        f.write(prefix+layer_a)
    with open('debug_outputs/layer_b.gcode','w') as f:
        f.write(prefix+layer_b)
