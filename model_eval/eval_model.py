from ar_gen import one_layer_comparison
from gcode_render import parse_gcode, plot_layer
import argparse
import pdb
import numpy as np
import matplotlib.pyplot as plt
import os

def iou_list(pred, gt):
    pred_layer_dict = parse_gcode(pred)
    gt_layer_dict = parse_gcode(gt)
    assert len(pred_layer_dict) == len(gt_layer_dict), "Number of layers do not match"

    iou_lst = []
    for i in range(len(pred_layer_dict)):
        pred_layer = plot_layer(pred_layer_dict,i)
        gt_layer = plot_layer(gt_layer_dict,i)

        # intersection = np.logical_and(pred, gt)
        intersection = pred_layer * gt_layer
        union = np.stack([pred_layer,gt_layer]).max(axis=0)
        # union = np.logical_or(pred, gt)
    
        iou = np.sum(intersection) / np.sum(union)
        iou_lst.append(iou)

    return iou_lst



if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model")
    args = parser.parse_args()

    experiment_id = args.model_path.split('/')[-2]
    args.experiment_id = experiment_id

    validation_data = os.listdir("/vast/km3888/paired_gcode/thingiverse_10k_marlin/")[6000:]
    val_example = validation_data[0]
    
    gt_layers = []
    pred_layers = []
    for layer_idx in range(1, 5):
        gt_layer,pred_layer = one_layer_comparison(args.model_path,layer_idx)
        gt_layers.append(gt_layer)
        pred_layers.append(pred_layer)
    
    pred_gcode = ";LAYER_CHANGE".join(pred_layers)
    gt_gcode = ";LAYER_CHANGE".join(gt_layers)
    iou_lst = iou_list(pred_gcode, gt_gcode)
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