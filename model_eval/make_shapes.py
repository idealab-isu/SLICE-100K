from ar_gen import one_layer_comparison, get_model
from gcode_render import parse_gcode, plot_layer,plot_layer_rectangle
import argparse
import pdb
import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import random
import copy
import re
from gcode_preprocessing import relative_extrusion, absolute_extrusion, get_layers
random.seed(42)

def get_eval_layers():
    sailfish_data_dir = "/vast/km3888/paired_gcode/thingiverse_10k_sailfish"  
    marlin_data_dir = "/vast/km3888/paired_gcode/thingiverse_10k_marlin"

    data_files = os.listdir(sailfish_data_dir)
    eval_data_files = data_files[6000:6010]
    output_layers = []
    for i,data_path in enumerate(eval_data_files):
        sailfish_data_path = os.path.join(sailfish_data_dir,data_path)
        marlin_data_path = sailfish_data_path.replace("sailfish","marlin")

        sailfish_file = open(sailfish_data_path,'r').read()
        marlin_file = open(marlin_data_path,'r').read()

        sailfish_layers = sailfish_file.split(';LAYER_CHANGE')
        marlin_layers = marlin_file.split(';LAYER_CHANGE')

        combined_layers = list(zip(sailfish_layers,marlin_layers))
        output_layers.extend(combined_layers[1:])
    return output_layers

def get_eval_shapes(num_files=10):
    sailfish_data_dir = "/vast/km3888/paired_gcode/thingiverse_10k_sailfish"  
    marlin_data_dir = "/vast/km3888/paired_gcode/thingiverse_10k_marlin"

    data_files = os.listdir(sailfish_data_dir)
    eval_data_files = data_files[6000:6000+num_files]
    output_shapes = []
    for i,data_path in enumerate(eval_data_files):
        sailfish_data_path = os.path.join(sailfish_data_dir,data_path)
        marlin_data_path = sailfish_data_path.replace("sailfish","marlin")

        sailfish_file = open(sailfish_data_path,'r').read()
        marlin_file = open(marlin_data_path,'r').read()

        output_shapes.append((sailfish_file,marlin_file))
    
    return output_shapes

def iou_list(pred_lst, gt_lst,output_dir):
    iou_lst = []
    for i,(pred,gt) in enumerate(zip(pred_lst, gt_lst)):
        pred_layer_dict = parse_gcode(pred)
        gt_layer_dict = parse_gcode(gt)
        if not len(pred_layer_dict):
            continue
        assert all([x is not None for x in pred_layer_dict.keys()])
        assert len(pred_layer_dict) == len(gt_layer_dict), "Number of layers do not match"
        gt_path = os.path.join(output_dir,str(i)+"_gt.png")
        pred_path = os.path.join(output_dir,str(i)+"_pred.png")

        pred_layer = plot_layer_rectangle(pred_layer_dict,pred_path,0)
        gt_layer = plot_layer_rectangle(gt_layer_dict,gt_path,0)

        intersection = pred_layer * gt_layer
        union = np.stack([pred_layer,gt_layer]).max(axis=0)
    
        iou = np.sum(intersection) / np.sum(union)
        iou_lst.append(iou)

    return np.array(iou_lst)

def iou_stats(iou_lst):
    iou_lst = np.array(iou_lst)
    stats = {
    "IOU": np.mean(iou_lst),
    "Median IOU": np.median(iou_lst),
    "Max IOU": np.max(iou_lst),
    "Min IOU": np.min(iou_lst),
    "Std IOU": np.std(iou_lst),
    "Variance IOU": np.var(iou_lst),
    "IOU list": iou_lst,
    "Number of layers": len(iou_lst)
    }
    return stats

def do_translation(model_path,num_shapes,output_dir):
    # load model and tokenizer
    model,tokenizer = get_model(model_path)
    print("Model loaded")

    os.makedirs(output_dir,exist_ok=True)
    eval_shapes = get_eval_shapes(num_shapes)
    output_dir = os.path.join(output_dir)
    stats_lst = []
    for shape_idx in tqdm(range(len(eval_shapes))):
        # Convert shapes to relative extrusions and split into layers
        sailfish_shape,marlin_shape = eval_shapes[shape_idx]
        relative_marlin,relative_sailfish = relative_extrusion(marlin_shape,sailfish_shape)
        relative_layers = get_layers([(relative_sailfish,relative_marlin)])
        assert relative_layers[0][0] == relative_sailfish[:len(relative_layers[0][0])], "First layer does not match"
        assert relative_layers[0][1] == relative_marlin[:len(relative_layers[0][1])], "First layer does not match"
        # Translate each layer
        pred_marlin_layers = [relative_layers[0][1]]
        for layer_idx in tqdm(range(1,len(relative_layers))):
            sailfish_layer = relative_layers[layer_idx][0]
            _,pred_layer = one_layer_comparison(args.model_path,sailfish_layer,model,tokenizer)
            # pdb.set_trace()
            pred_marlin_layers.append(pred_layer)
            if layer_idx == 1:
                # save raw text of pred_layer 
                layer_path = os.path.join(output_dir,f"layer_{shape_idx}.txt")
                with open(layer_path,'w') as f:
                    f.write(pred_layer)
                gt_layer_path = os.path.join(output_dir,f"gt_layer_{shape_idx}.txt")
                with open(gt_layer_path,'w') as f:
                    f.write(marlin_shape)
                
        # Join layers together and convert back to absolute extrusion
        relative_marlin_pred = "".join(pred_marlin_layers)
        pred_marlin, _ = absolute_extrusion(relative_marlin_pred,sailfish_shape)
        
        # Write pred_marlin to file
        output_path = os.path.join(output_dir,f"shape_{shape_idx}.gcode")
        with open(output_path,'w') as f:
            f.write(pred_marlin)

        #also save relative_marlin_pred
        relative_output_path = os.path.join(output_dir,f"relative_shape_{shape_idx}.gcode")
        with open(relative_output_path,'w') as f:
            f.write(relative_marlin_pred)

        # also save sailfish_shape
        sailfish_output_path = os.path.join(output_dir,f"sailfish_shape_{shape_idx}.gcode")
        with open(sailfish_output_path,'w') as f:
            f.write(sailfish_shape)
        
        # also save ground truth marlin shape
        marlin_output_path = os.path.join(output_dir,f"marlin_shape_{shape_idx}.gcode")
        with open(marlin_output_path,'w') as f:
            f.write(marlin_shape)

        # also save relative sailfish
        relative_sailfish_output_path = os.path.join(output_dir,f"relative_sailfish_{shape_idx}.gcode")
        with open(relative_sailfish_output_path,'w') as f:
            f.write(relative_sailfish)
            
        # IOU is layer-wise so have to convert back to split layers
        iou_lst = iou_list(pred_marlin.split(";LAYER_CHANGE")[1:],marlin_shape.split(";LAYER_CHANGE")[1:],output_dir)
        stats = iou_stats(iou_lst)
        stats_lst.append(stats)

    # Write stats for each shape to one file
    stats_path = os.path.join(output_dir,"stats.txt")
    with open(stats_path,'w') as f:
        for stat in stats_lst:
            f.write(str(stat))
            f.write("\n")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model")
    parser.add_argument("--num_shapes", type=int, default=10, help="Number of shapes to generate")
    parser.add_argument("--output_base_dir", type=str, required=True)
    args = parser.parse_args()

    # Get output directory
    experiment_id = args.model_path.strip('/').split('/')[-2]
    output_dir = os.path.join(args.output_base_dir,experiment_id)

    do_translation(args.model_path,args.num_shapes,output_dir)