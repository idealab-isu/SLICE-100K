import pdb
from preprocess_utils import debug

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

def insert_delimiters_F(content):
    content_lines = content.split('\n')
    output_content = []
    split_happened = False
    recent_split = True
    for line in content_lines:
        if 'X' in line and 'F' in line:
            if split_happened and not recent_split:
                recent_split = True
                output_content.append('</del>')
            split_happened = True
        elif recent_split and 'G' in line and 'Y' in line and 'X' in line and 'E' in line:
            recent_split = False
            
        output_content.append(line)
    return '\n'.join(output_content)

def make_hash_idx(layer_b_blocks):
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
                debug(layer_a,layer_b,layer_a_delimited,layer_b_delimited)
                # pdb.set_trace()
                raise Exception ('Duplicate line segment')
            lookup[line_seg] = idx_b
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
    layer_a_delimited = insert_delimiters_F(layer_a)
    layer_b_delimited = insert_delimiters_F(layer_b)
    layer_a_blocks = layer_a_delimited.strip().split('</del>\n')
    layer_b_blocks = layer_b_delimited.strip().split('</del>\n')
    debug(layer_a,layer_b,layer_a_delimited,layer_b_delimited)
    # if len(layer_a_blocks)!=len(layer_b_blocks):
    #     debug(layer_a,layer_b)
    #     # pdb.set_trace()
    #     raise Exception('Different number of blocks')
    #Create hash index of blocks in layer_b
    lookup = make_hash_idx(layer_b_blocks)
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
            debug(layer_a,layer_b,layer_a_delimited,layer_b_delimited)
            # pdb.set_trace()
            raise Exception('Could not find a matching block')
    if len(b_found)<len(layer_b_blocks):
        # pdb.set_trace()
        raise Exception('Not surjective')
    flipped = [None for _ in range(len(layer_b_blocks))]
    for idx_b,(idx_a,line_seg) in b_found.items():
        flipped[idx_a]=layer_b_blocks[idx_b]
    flipped_text = ''.join(flipped)
    return flipped_text

def flip_on_perimeters(text_a,text_b):
    text_a_layers = text_a.strip().split(';LAYER_CHANGE')
    text_b_layers = text_b.strip().split(';LAYER_CHANGE')
    zipped_layers = zip(text_a_layers[1:],text_b_layers[1:])
    assert len(text_a_layers)==len(text_b_layers)
    successes = 0
    failures = 0
    output_a_list = [text_a_layers[0]]
    output_b_lst = [text_b_layers[0]]
    # pdb.set_trace()
    for i,(layer_a,layer_b) in enumerate(zipped_layers):
        output_a_list.append(layer_a)

        # flipped_layer_b = flip_layer_on_perimeters(layer_a,layer_b)
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

