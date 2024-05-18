from ar_gen import one_layer_comparison
from gcode_render import parse_gcode, plot_layer
import argparse
import pdb
import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import random
import copy
import re
from gcode_preprocessing import sailfish_relative_extrusion, marlin_relative_extrusion, sailfish_absolute_extrusion, marlin_absolute_extrusion
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

def iou_list(pred_lst, gt_lst,experiment_id):
    iou_lst = []
    for i,(pred,gt) in enumerate(zip(pred_lst, gt_lst)):
        if i==6:
            pdb.set_trace()
        pred_layer_dict = parse_gcode(pred)
        gt_layer_dict = parse_gcode(gt)
        assert len(pred_layer_dict) == len(gt_layer_dict), "Number of layers do not match"
        pred_layer = plot_layer(pred_layer_dict,str(i)+"_pred_"+experiment_id,0)
        gt_layer = plot_layer(gt_layer_dict,str(i)+"_gt_"+experiment_id,0)

        # intersection = np.logical_and(pred, gt)
        intersection = pred_layer * gt_layer
        union = np.stack([pred_layer,gt_layer]).max(axis=0)
        # union = np.logical_or(pred, gt)
    
        iou = np.sum(intersection) / np.sum(union)
        iou_lst.append(iou)

    return np.array(iou_lst)

def iou_stats(iou_lst):
    iou_lst = np.array(iou_lst)
    print(iou_lst)
    print(f"IOU: {np.mean(iou_lst)}")
    print(f"Median IOU: {np.median(iou_lst)}")
    print(f"Max IOU: {np.max(iou_lst)}")
    print(f"Min IOU: {np.min(iou_lst)}")
    print(f"Std IOU: {np.std(iou_lst)}")
    print(f"Variance IOU: {np.var(iou_lst)}")
    print(f"IOU list: {iou_lst}")
    print(f"Number of layers: {len(iou_lst)}")

    plt.figure(figsize=(10, 8))
    plt.hist(iou_lst, bins=20, color='blue', alpha=0.7)
    plt.title('IOU Distribution')
    plt.xlabel('IOU')
    plt.ylabel('Frequency')
    plt.savefig("renders/iou_distribution.png")
    img = plt.imread("renders/iou_distribution.png")
    img = np.array(img)
    img = img[:, :, 0]
    plt.imshow(img)
    plt.show()
    print("IOU distribution saved as renders/iou_distribution.png")
    print("Done!")

def do_eval(model_path,num_layers,rel,experiment_id):
    eval_layers = get_eval_layers()
    # random.shuffle(eval_layers)
    eval_layers = eval_layers[:num_layers]
    total_num_layers = len(eval_layers)
    gt_layers = []
    pred_layers = []
    # pdb.set_trace()
    for i in tqdm(range(len(eval_layers))):
        sailfish_layer,marlin_layer = eval_layers[i]
        # sailfish_layer = sailfish_layer[:5000]
        # marlin_layer = marlin_layer[:5000]
        if rel:
            sailfish_layer,_ = sailfish_relative_extrusion(sailfish_layer)
            sailfish_layer = sailfish_layer.replace("<e>","")
        _,pred_layer = one_layer_comparison(args.model_path,sailfish_layer)
        gt_layer = marlin_layer
        gt_layers.append(gt_layer)
        pdb.set_trace()
        if rel:
            pred_layer,_ = marlin_absolute_extrusion(pred_layer)
        pred_layers.append(pred_layer)
        # write gt_layer and pred_layer to files
        gt_file = open(f"renders/gt_{i}.gcode",'w')
        gt_file.write(gt_layer)
        gt_file.close()
        pred_file = open(f"renders/pred_{i}.gcode",'w')
        pred_file.write(pred_layer)
        pred_file.close()
    iou_lst = iou_list(pred_layers, gt_layers,experiment_id)
    iou_dist = (1-iou_lst)**2
    mean_iou_dist = np.mean(iou_dist)
    root_mean_iou_dist = np.sqrt(mean_iou_dist)
    print(f"Root Mean IOU Distance: {root_mean_iou_dist}")
    iou_stats(iou_lst)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model")
    args = parser.parse_args()

    experiment_id = args.model_path.split('/')[-2]
    args.experiment_id = experiment_id
    num_layers = 1
    rel = True
    do_eval(args.model_path,num_layers,rel,experiment_id)
    validation_data = os.listdir("/vast/km3888/paired_gcode/thingiverse_10k_marlin/")[6000:]    