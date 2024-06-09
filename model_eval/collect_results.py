import os
import pdb
import prettytable

iou_paths = ["base_gpt2/iou_stats.txt","47185774_0/iou_stats.txt","47163343_0/iou_stats.txt","47015772_0/iou_stats.txt","47015772_1/iou_stats.txt","47015772_2/iou_stats.txt","47015772_3/iou_stats.txt"]
threshes = [0.9,0.95,0.98,0.99,0.995,0.999]
base_dir = None #add base_dir if using result collection script

thresh_lst = []
for iou_path in iou_paths:
    iou_path = os.path.join(base_dir,iou_path)
    with open(iou_path) as f:
        lines = f.readlines()
    joined_text = "".join([x.replace('\n','') for x in lines])
    joined_text = joined_text.replace("array(","").replace(")","").replace("dtype=float32,","")
    iou_list = eval(joined_text)["IOU list"]
    iou_list = iou_list + [0]*(100-len(iou_list))
    print("="*8)
    print(iou_path)
    print(len(iou_list))
    # pdb.set_trace()

    thresh_lst_i = []
    for thresh in threshes:
        num_above = sum([bool(x>thresh) for x in iou_list])
        thresh_lst_i.append(num_above/len(iou_list))
        print("thresh: %s, num above:%s"  %(thresh,num_above/len(iou_list)))
    thresh_lst.append(thresh_lst_i)

#make table where each row shows all the different num_above values for each iou_path
table = prettytable.PrettyTable()
table.field_names = ["IOU Path"] + [str(x) for x in threshes]
for i in range(len(iou_paths)):
    table.add_row([iou_paths[i]] + thresh_lst[i])
print(table)
