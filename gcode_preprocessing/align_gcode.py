import json
from prettytable import PrettyTable
from transformers import AutoTokenizer
import pdb
import os
import sys
import argparse
access_token = "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"
prefix = "G1 Z5 F5000\nG21\nG90 \n; Filament gcode\nM127\n;LAYER_CHANGE\n"


def find_same(text_a_lines,text_b_lines,i,start_j):
    """
    Finds the first line in text_b that is the same as line_i in text_a.

    Args:
        text_a: The first text to compare.
        text_b: The second text to compare.
        line_i: The line in text_a to compare.

    Returns:
        The index of the first line in text_b that is the same as line_i in text_a.
    """
    #TODO, make this operate on pairs of layers instead of pairs of files
    for j,line in enumerate(text_b_lines[start_j:]):
        if not "X" in line or not "Y" in line:
            continue
        #make sure that we're looking at a coordinate placement line
        line_i = text_a_lines[i].split(' E')[0]
        #remove the extrusion value since that varies across flavors
        line_j = line.split(' E')[0]
        if line_j==line_i:
            return j+start_j
    return -1

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

def aligned_chunks(text_a,text_b,max_lines):
    if not (isinstance(text_a,str) and isinstance(text_b,str)):
        pdb.set_trace()
    text_a_lines = text_a.strip().split('\n')
    text_b_lines = text_b.strip().split('\n')
    debug(text_a,text_b)
    num_lines = len(text_a_lines)
    start_i = 0
    end_i = min(start_i+max_lines,num_lines)
    start_j = 0
    chunks = []
    while start_i<num_lines:
        if num_lines - start_i<=max_lines:
            chunk_a = "".join( x+"\n" for x in text_a_lines[start_i:])
            chunk_b = "".join( x+"\n" for x in text_b_lines[start_j:])
            chunks.append({"text_1":chunk_a,"text_2":chunk_b})
            break
        end_j = find_same(text_a_lines,text_b_lines,end_i,start_j)
        if (end_j-start_j)>2*(end_i-start_i):
            debug_a = "\n".join(text_a_lines[:end_i])
            debug_b = "\n".join(text_b_lines[:end_j])
            debug(debug_a,debug_b)
            pdb.set_trace()
            raise Exception("Something bad happened")
        if end_j!=-1 and ((end_j-start_j)*2 < (end_i-start_i)):
            # check whether text_a_lines[i] is a duplicate within its own chunk
            text_a_chunk = text_a_lines[start_i:end_i]
            text_a_chunk_no_e = [x.split(' E')[0] for x in text_a_chunk]
            if text_a_lines[end_i].split(' E')[0] in text_a_chunk_no_e:
                end_i-=1
                continue
            else:
                print('-'*8)
                print("start_i:",start_i)
                print("end_i:",end_i)
                print("start_j:",start_j)
                print("end_j:",end_j)
                print("text_a_lines[start_i]:",text_a_lines[start_i])
                print("text_a_lines[end_i]:",text_a_lines[end_i])
                print("text_b_lines[start_j]:",text_b_lines[start_j])
                print("text_b_lines[end_j]:",text_b_lines[end_j])
                relevant_a = "\n".join(text_a_lines[start_i-20:end_i+20])
                relevant_b = "\n".join(text_b_lines[start_j-20:end_j+20])
                debug(relevant_a,relevant_b)
                pdb.set_trace()
        if end_j==-1:
            if (end_i-start_i)<max_lines//2:
                print('start_i:',start_i)
                print('end_i:',end_i)
                print(text_a_lines[start_i])
                print(text_a_lines[end_i])
                # pdb.set_trace()
                print('broken')
                for chunk in chunks:
                    a = chunk["text_1"]
                    b = chunk["text_2"]
                    # convert_strings_to_table(a,b)
                # convert_strings_to_table(text_,text_b)
                pdb.set_trace()
                raise Exception("Hey what's going on here")
            end_i-=1
        else:
            chunk_b = "".join( x+"\n" for x in text_b_lines[start_j:end_j+1])
            chunk_a = "".join( x+"\n" for x in text_a_lines[start_i:end_i+1])
            chunks.append({"text_1":chunk_a,"text_2":chunk_b})
            start_i = end_i+1
            start_j = end_j+1
            end_i = min(start_i+max_lines,num_lines)

    return chunks

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
        print('path a:',path_a)
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
        # pdb.set_trace()

        content_a,content_b = flip_on_perimeters(content_a,content_b)
        assert '</del>' not in content_b
    return output

def debug(layer_a,layer_b):
    # save all of layer_a and layer_b along with their delimited counterparts
    layer_a_delimited = insert_delimiters_F(layer_a).replace('</del>','(</del>)')
    layer_b_delimited = insert_delimiters_F(layer_b).replace('</del>','(</del>)')
    with open('layer_a_delimited.gcode','w') as f:
        f.write(prefix+layer_a_delimited)
    with open('layer_b_delimited.gcode','w') as f:
        f.write(prefix+layer_b_delimited)
    with open('layer_a.gcode','w') as f:
        f.write(prefix+layer_a)
    with open('layer_b.gcode','w') as f:
        f.write(prefix+layer_b)

def remove_nums(s):
    # remove all numbers from a string
    if 'F' in s:
        return ''.join([i for i in s if not i.isdigit()])
    return s

def make_line_seg(i,lines):
    line_1 = lines[i]
    line_2 = None
    if i+1<len(lines):
        line_2 = lines[i+1]
    line_3 = None
    if i+2<len(lines):
        line_3 = lines[i+2]

    line_1 = remove_nums(line_1)
    line_seg_1 = line_1.split(' E')[0]
    if 'E' in line_1 :
        line_seg_1 += 'E'

    line_2 = '</d>'
    if line_2 is not None:
        line_2 = remove_nums(line_2)
        line_seg_2 = line_2.split(' E')[0]
        if 'E' in line_2:
            line_seg_2 += 'E'

    line_seg_3 = '</d>'
    if line_3 is not None:
        line_3 = remove_nums(line_3)
        line_seg_3 = line_3.split(' E')[0]
        if 'E' in line_3:
            line_seg_3 += 'E'

    disregard=True
    for line_seg in [line_seg_1,line_seg_2,line_seg_3]:
        if not((len(line_seg.split(' '))<2) or ('.' not in line_seg) or ('F' in line_seg)):
            disregard=False
    line_seg_combined = line_seg_1 + ' ' + line_seg_2 + ' ' + line_seg_3

    return line_seg_combined,disregard

def flip_on_perimeters(text_a,text_b):
    text_a_layers = text_a.strip().split(';LAYER_CHANGE')
    text_b_layers = text_b.strip().split(';LAYER_CHANGE')
    assert len(text_a_layers)==len(text_b_layers)
    successes = 0
    failures = 0
    output_a_list = [text_a_layers[0]]
    output_b_lst = [text_b_layers[0]]
    pdb.set_trace()
    for i in range(1,len(text_a_layers)):
        layer_a = text_a_layers[i]
        output_a_list.append(layer_a)
        layer_b = text_b_layers[i]
        ############
        # flipped_layer_b = flip_layer_on_perimeters(layer_a,layer_b)
        # output_b_lst.append(flipped_layer_b)
        ############
        try:
            flipped_layer_b = flip_layer_on_perimeters(layer_a,layer_b)
            output_b_lst.append(flipped_layer_b)
            successes+=1
        except Exception as e:
            failures+=1
            output_a_list.pop()
    print('%s/%s' % (successes,(successes+failures)))
    if successes==0:
        pdb.set_trace()
    # join all the modified layers together with the original delimiter
    output_a = ';LAYER_CHANGE'.join(output_a_list)
    output_b = ';LAYER_CHANGE'.join(output_b_lst)
    return output_a,output_b

def make_hash_idx(layer_b):
    lookup = {}
    for idx_b,block_b in enumerate(layer_b_blocks):
        if idx_b==0:
            continue
        block_b_lines = block_b.strip().split('\n')
        for i in range(len(block_b_lines)):
            line_seg,disregard = make_line_seg(i,block_b_lines)
            if disregard:
                continue
            if line_seg in lookup and lookup[line_seg]!=idx_b:
                debug(layer_a,layer_b)
                # pdb.set_trace()
                raise Exception ('Duplicate line segment')
            lookup[line_seg] = [idx_b]
    return lookup

def make_hash_idx_solo(layer_b):
    #same as above function but only uses one line at a time
    #gives more collisions but reduces false negatives
    lookup = {}
    for idx_b,block_b in enumerate(layer_b_blocks):
        if idx_b==0:
            continue
        block_b_lines = block_b.strip().split('\n')
        for i in range(len(block_b_lines)):
            line_seg,disregard = make_line_seg(i,block_b_lines)
            line_seg = line_seg.split('</del>')[0]
            if disregard:
                continue
            if line_seg not in lookup:
                lookup[line_seg] = []
            lookup[line_seg].append(idx_b)
    return lookup

def flip_layer_on_perimeters(layer_a,layer_b):
    layer_a_blocks = insert_delimiters_F(layer_a).strip().split('</del>\n')
    layer_b_blocks = insert_delimiters_F(layer_b).strip().split('</del>\n')
    debug(layer_a,layer_b)
    if len(layer_a_blocks)!=len(layer_b_blocks):
        debug(layer_a,layer_b)
        raise Exception('Different number of blocks')
    #Create hash index of blocks in layer_b
    lookup = make_hash_idx(layer_b)
    #Match blocks in layer_a to blocks in layer_b using hash index
    b_found = {}
    for idx_a,block_a in enumerate(layer_a_blocks):
        if idx_a==0:
            b_found[0]=(0,'')
            continue
        block_a_lines = block_a.strip().split('\n')
        found=False
        for i in range(len(block_a_lines)):
            line_seg,disregard = make_line_seg(i,block_a_lines)
            if disregard:
                continue

            if line_seg in lookup:
                idx_b = lookup[line_seg]
                if idx_b in b_found:
                    # pdb.set_trace()
                    raise Exception('Not injective')
                b_found[idx_b]=(idx_a,line_seg)
                # if idx_b!=idx_a:
                #     try:
                #         layer_b_blocks[idx_b],layer_b_blocks[idx_a] = layer_b_blocks[idx_a],layer_b_blocks[idx_b]
                #     except IndexError as e:
                #         pdb.set_trace()
                    # flip the block
                found=True
                break

        if not found:
            # debug(layer_a,layer_b)
            # pdb.set_trace()
            pdb.set_trace()
            raise Exception('Could not find a matching block')

    if len(b_found)<len(layer_b_blocks):
        # pdb.set_trace()
        raise Exception('Not surjective')
    flipped = [None for _ in range(len(layer_b_blocks))]
    for idx_b,(idx_a,line_seg) in b_found.items():
        flipped[idx_a]=layer_b_blocks[idx_b]
    flipped_text = ''.join(flipped)
    return flipped_text

def insert_delimiters_F(content):
    content_lines = content.split('\n')
    output_content = []
    split_happened = False
    recent_split = True
    for line in content_lines:
        if 'X' in line and 'Y' in line and 'F' in line:
            if split_happened and not recent_split:
                recent_split = True
            split_happened = True
        elif recent_split and 'G' in line and 'Y' in line and 'X' in line and 'E' in line:
            recent_split = False
            output_content.append('</del>')
        output_content.append(line)
    return '\n'.join(output_content)

def main(args):
    data = get_data(args.n_files)
    # align all the G-code pairs so that the Marlin and Sailfish both create 
    # all of the shape's contours in the same order
    aligned_gcode = []
    for gcode_a,gcode_b in data:
        flipped_a,flipped_b = flip_on_perimeters(gcode_a,gcode_b)
        aligned_gcode.append((flipped_a,flipped_b))

    #create chunks of size small enough to fit in transformer context window
    chunk_list = []
    for aligned_a,aligned_b in aligned_gcode:
        chunks = aligned_chunks(aligned_a,aligned_b,args.chunk_size)
        chunk_list.extend(chunks)

    make_json(chunk_list)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_files", type=int, default=200)
    parser.add_argument("--chunk_size", type=int, default=15)
    args = parser.parse_args()

    main(args)