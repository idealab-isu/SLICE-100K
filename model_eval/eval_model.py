from ar_gen import one_layer_comparison, get_model
from gcode_render import parse_gcode, plot_layer, plot_layer_rectangle
import argparse
import pdb
import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import random
import copy
import re
from gcode_preprocessing import absolute_extrusion, relative_extrusion, get_layers, marlin_absolute_extrusion
random.seed(42)

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
        gt_path = os.path.join(output_dir,str(i)+"_gt_rec.png")
        pred_path = os.path.join(output_dir,str(i)+"_pred_rec.png")
        pred_layer = plot_layer_rectangle(pred_layer_dict,pred_path)
        gt_layer = plot_layer_rectangle(gt_layer_dict,gt_path)

        # intersection = np.logical_and(pred, gt)
        intersection = pred_layer * gt_layer
        union = np.stack([pred_layer,gt_layer]).max(axis=0)
        # union = np.logical_or(pred, gt)
    
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

def do_eval(model_path,num_layers,rel,output_dir):
    #load model and tokenizer
    model,tokenizer = get_model(model_path)
    print("Model loaded")

    eval_shapes = get_eval_shapes()
    eval_layers = []
    # Get relative layers to sample from
    for shape_idx in range(len(eval_shapes)):
        sailfish_shape,marlin_shape = eval_shapes[shape_idx]
        abs_eval_layers = get_layers([(sailfish_shape,marlin_shape)])[1:]
        relative_marlin,relative_sailfish = relative_extrusion(marlin_shape,sailfish_shape)
        rel_eval_layers = get_layers([(relative_sailfish,relative_marlin)])[1:]
        eval_layers.extend(zip(rel_eval_layers,abs_eval_layers))
    
    print("Started translation")
    random.shuffle(eval_layers)
    eval_layers = eval_layers[:num_layers]
    pred_layers = []
    gt_layers = []
    for i in tqdm(range(len(eval_layers))):
        rel_layers,abs_layers = eval_layers[i]
        rel_sailfish,rel_marlin = rel_layers
        abs_sailfish,abs_marlin = abs_layers

        #Translate each layer, get predicted relative marlin
        _,pred_rel_marlin = one_layer_comparison(args.model_path,rel_sailfish,model,tokenizer)
        pred_abs_marlin,_ = marlin_absolute_extrusion(pred_rel_marlin)

        pred_layers.append(pred_abs_marlin)
        gt_layers.append(abs_marlin)
    print("Finished translation")
    iou_lst = iou_list(pred_layers, gt_layers,output_dir)
    iou_dist = (1-iou_lst)**2
    mean_iou_dist = np.mean(iou_dist)
    root_mean_iou_dist = np.sqrt(mean_iou_dist)
    print(f"Root Mean IOU Distance: {root_mean_iou_dist}")
    stats = iou_stats(iou_lst)
    # write iou stats to text file in output directory
    with open(os.path.join(output_dir,"iou_stats.txt"),'w') as f:
        f.write(str(stats))


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model")
    parser.add_argument("--output_base_dir", type=str, required=True)
    parser.add_argument("--num_layers", type=int, default=10)
    args = parser.parse_args()

    # set up output directory
    experiment_id = args.model_path.strip('/').split('/')[-2]
    if "openai" in args.model_path:
        experiment_id = 'base_gpt2'
    if "meta" in args.model_path or "llama" in args.model_path:
        experiment_id = 'base_llama2'
    output_dir = os.path.join(args.output_base_dir,experiment_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    args.experiment_id = experiment_id

    rel = True
    do_eval(args.model_path,args.num_layers,rel,output_dir)