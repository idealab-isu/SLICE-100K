from ar_gen import one_layer_comparison
from gcode_render import parse_gcode, plot_layer
import argparse
import pdb
import numpy as np
import matplotlib.pyplot as plt


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

    gt_layers = []
    pred_layers = []
    for layer_idx in range(1, 5):
        # gt_layer,pred_layer = one_layer_comparison(args,layer_idx)
        gt_layer,pred_layer = one_layer_comparison(args,layer_idx)
        gt_layers.append(gt_layer)
        pred_layers.append(pred_layer)
    
    pred_gcode = ";LAYER_CHANGE".join(pred_layers)
    gt_gcode = ";LAYER_CHANGE".join(gt_layers)
    iou_lst = iou_list(pred_gcode, gt_gcode)
    iou_lst = np.array(iou_list)
    print(iou_list)
    print(f"IOU: {np.mean(iou_list)}")
    print(f"Median IOU: {np.median(iou_list)}")
    print(f"Max IOU: {np.max(iou_list)}")
    print(f"Min IOU: {np.min(iou_list)}")
    print(f"Std IOU: {np.std(iou_list)}")
    print(f"Variance IOU: {np.var(iou_list)}")
    print(f"IOU list: {iou_list}")
    print(f"Number of layers: {len(iou_list)}")

    plt.figure(figsize=(10, 8))
    plt.hist(iou_list, bins=20, color='blue', alpha=0.7)
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