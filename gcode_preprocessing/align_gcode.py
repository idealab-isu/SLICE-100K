import json
from prettytable import PrettyTable
from transformers import AutoTokenizer
import pdb
import os
import sys
import argparse

from chunking import aligned_chunks
from contour_flipping import flip_on_perimeters

access_token = "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"

def convert_strings_to_table(text_1,text_2):    
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

def make_json(chunk_list):
    out_list = []
    for chunk in chunk_list:
        a = chunk["text_1"]
        b = chunk["text_2"]
        out_dict = {}
        out_dict['text']=f"Instruction: Translate the inputted GCode from Marlin to Sailfish \n Input:{a} \n Output:{b}" 
        out_list.append(out_dict)
    json.dump(out_list, open(f"/vast/km3888/paired_gcode/test_aligned_chunks_{n_files}_{chunk_size}.json", 'w'))
    
def get_data(n_files):
    gcode_path_a = "/vast/km3888/paired_gcode/thingiverse_10k_marlin"
    gcode_path_b = "/vast/km3888/paired_gcode/thingiverse_10k_sailfish"
    
    output = []
    for i,file_name_a in enumerate(os.listdir(gcode_path_a)[:n_files]):
    # for i,file_name_a in enumerate(os.listdir(gcode_path_a)[25:26]):
        path_a = os.path.join(gcode_path_a,file_name_a)
        path_b = path_a.replace('marlin', 'sailfish')
        if not os.path.exists(path_b):
            print(f'{path_b} does not exist')
            continue

        file_a = open(path_a, 'r').read()
        file_b = open(path_b, 'r').read()

        debug_marlin = '\n'.join(file_a.split('\n')[:500])
        with open('og_marlin.gcode', 'w') as f:
            f.write(debug_marlin)

        content_a = file_a.split('G28')[1]
        content_b = file_b.split('G28')[1]
        
        output.append((content_a,content_b))
    return output

def main(args):
    data = get_data(args.n_files)
    # align all the G-code pairs so that the Marlin and Sailfish both create 
    # all of the shape's contours in the same order
    aligned_gcode = []
    successes = 0
    failures = 0
    for i,(gcode_a,gcode_b) in enumerate(data):
        flipped_a,flipped_b = flip_on_perimeters(gcode_a,gcode_b)
        # try:
        #     flipped_a,flipped_b = flip_on_perimeters(gcode_a,gcode_b)
        #     aligned_gcode.append((flipped_a,flipped_b))
        #     successes+=1
        # except Exception as e:
        #     failures+=1
    print(f'{successes}/{successes+failures} files successfully aligned')

    #create chunks of size small enough to fit in transformer context window
    chunk_list = []
    successes = 0
    failures = 0
    for aligned_a,aligned_b in aligned_gcode:
        try:
            chunks = aligned_chunks(aligned_a,aligned_b,args.chunk_size)
            chunk_list.extend(chunks)
        except:
            failures+=1
    print(f'{successes}/{successes+failures} chunks successfully created')

    make_json(chunk_list)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_files", type=int, default=200)
    parser.add_argument("--chunk_size", type=int, default=15)
    args = parser.parse_args()

    main(args)