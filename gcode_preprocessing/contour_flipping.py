import pdb
from preprocess_utils import debug

def remove_nums(s):
    # remove all numbers from a string
    if 'F' in s:
        return ''.join([i for i in s if not i.isdigit()])
    parts = s.split(' ')
    s_fixed = " ".join([part for part in parts if not 'S' in part])
    return s_fixed

def make_line_seg(i,lines):
    line_1 = lines[i]
    if line_1==";END gcode for filament":
        return line_1, False
    if 'final' in line_1:
        return 'final', False
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
        if 'G92 E0' in line_2 or 'final' in line_2:
            pass 
        else:
            line_2 = remove_nums(line_2)
            line_seg_2 = line_2.split(' E')[0]
            if 'E' in line_2:
                line_seg_2 += 'E'

    line_seg_3 = '</d>'
    if line_3 is not None:
        if 'G92 E0' in line_3 or 'final' in line_3:
            pass
        else:
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

def insert_first_delimiter(content_a,content_b):
    content_a_before = content_a.split('G92 E0')[0] + 'G92 E0'
    content_a_after = 'G92 E0'.join(content_a.split('G92 E0')[1:])

    num_lines_a = len(content_a_before.split('\n'))
    content_b_before = content_b.split('\n')[:num_lines_a]
    content_b_after = content_b.split('\n')[num_lines_a:]

    content_b_before = '\n'.join(content_b_before)
    content_b_after = '\n'.join(content_b_after)
    return content_a_before,content_a_after,content_b_before,content_b_after

def insert_delimiters_F(content,debug=False):
    content_lines = content.split('\n')
    output_content = []
    split_happened = False
    recent_split = True
    added_delim = False
    if content_lines[-1]=='':
        content_lines.pop()
    for i,line in enumerate(content_lines):
        if debug:
            print(line)
            # pdb.set_trace()
        # old condition
        if ('G1' in line and 'F' in line  and not 'E' in line):
            if split_happened and not recent_split and i<len(content_lines)-1:
                recent_split = True
                output_content.append('</del>')
                addded_delim = True
            split_happened = True
            if added_delim:
                split_happened = False
                added_delim=False
        # old condition
        elif recent_split and 'G' in line and 'Y' in line and 'X' in line and 'E' in line:
        # recent_split and 'G' in line and 'Y' in line and 'X' in line and 'E' in line
        # elif recent_split and 'G' in line and 'E' in line and not 'F' in line:
            recent_split = False
            
        output_content.append(line)
    output_str = '\n'.join(output_content)
    return output_str

def make_hash_idx(layer_b_blocks):
    lookup = {}
    duplicate_segs = set()
    for idx_b,block_b in enumerate(layer_b_blocks):
        # if idx_b==0:
        #     continue
        block_b_lines = block_b.strip().split('\n')
        for i in range(len(block_b_lines)):
            line_seg,disregard = make_line_seg(i,block_b_lines)
            if disregard:
                continue
            if line_seg in lookup and lookup[line_seg]!=idx_b:
                # debug(layer_a,layer_b,layer_a_delimited,layer_b_delimited)
                duplicate_segs.add(line_seg)
                continue
            lookup[line_seg] = idx_b
    return lookup,duplicate_segs

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

def flip_layer_on_perimeters(layer_a_plain,layer_b_plain):
    content_a_before,content_a_after,content_b_before,content_b_after = insert_first_delimiter(layer_a_plain,layer_b_plain)
    content_a_after += '\n final'
    content_b_after += '\n final'
    layer_a = content_a_after
    layer_b = content_b_after

    layer_a_delimited = insert_delimiters_F(layer_a)
    layer_b_delimited = insert_delimiters_F(layer_b)
    layer_a_blocks = layer_a_delimited.strip().split('</del>\n')
    layer_b_blocks = layer_b_delimited.strip().split('</del>\n')
    debug(layer_a,layer_b,layer_a_delimited,layer_b_delimited)
    # first_60_lines_a = "\n".join(layer_a.strip().split('\n')[:60])
    # first_60_lines_b = "\n".join(layer_b.strip().split('\n')[:60])
    # layer_a_delimited = insert_delimiters_F(first_60_lines_a,debug=True)
    # layer_b_delimited = insert_delimiters_F(first_60_lines_b,debug=True)

    if len(layer_a_blocks)!=len(layer_b_blocks):
        debug(layer_a,layer_b)
        # pdb.set_trace()
        raise Exception('Different number of blocks')
    if len(layer_a_blocks)<=1:
        return content_a_before + content_a_after
    if layer_a_blocks[-1]=="":
        layer_a_blocks.pop()
    #Create hash index of blocks in layer_b
    lookup,duplicate_segs = make_hash_idx(layer_b_blocks)
    #Match blocks in layer_a to blocks in layer_b using hash index
    b_found = {}
    for idx_a,block_a in enumerate(layer_a_blocks):
        # if idx_a==0:
        #     b_found[0]=(0,'')
        #     continue
        block_a_lines = block_a.strip().split('\n')
        found=False
        for i in range(len(block_a_lines)):
            line_seg,disregard = make_line_seg(i,block_a_lines)
            if disregard:
                continue
            if line_seg in lookup and line_seg not in duplicate_segs:
                idx_b = lookup[line_seg]
                if idx_b in b_found:
                    # pdb.set_trace()
                    raise Exception('Not injective')
                b_found[idx_b]=(idx_a,line_seg)
                found=True
                break

        if not found:
            debug(layer_a,layer_b,layer_a_delimited,layer_b_delimited)
            leftover_a = layer_a_blocks[idx_a:]
            leftover_b = [layer_b_blocks[i] for i in range(len(layer_b_blocks)) if i not in b_found.keys()]
            # pdb.set_trace()
            raise Exception('Could not find a matching block')
    if len(b_found)<len(layer_b_blocks):
        # pdb.set_trace()
        raise Exception('Not surjective')
    flipped = [None for _ in range(len(layer_b_blocks))]
    for idx_b,(idx_a,line_seg) in b_found.items():
        flipped[idx_a]=layer_b_blocks[idx_b]
    flipped_text = ''.join(flipped)
    full_text = content_a_before + flipped_text
    return full_text

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
    # if successes==0:
    #     pdb.set_trace()
    # join all the modified layers together with the original delimiter
    output_a = ';LAYER_CHANGE'.join(output_a_list)
    output_b = ';LAYER_CHANGE'.join(output_b_lst)
    output_a = output_a.replace('\n final','')
    output_b = output_b.replace('\n final','')
    return output_a,output_b