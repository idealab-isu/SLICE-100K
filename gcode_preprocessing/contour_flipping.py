import pdb
from preprocess_utils import debug

def remove_nums(s):
    """
    Removes all numbers from a string.

    Args:
        s (str): The input string.

    Returns:
        str: The string with all numbers removed.
    """
    if 'F' in s:
        return ''.join([i for i in s if not i.isdigit()])
    parts = s.split(' ')
    s_fixed = " ".join([part for part in parts if not 'S' in part])
    return s_fixed

def make_line_seg(i, lines):
    """
    Creates a maximally unique, flavor-agnostic representation of a line of G-Code
    that will be matched to the same line in another flavor via hashing

    To reduce the number of duplicate points in different parts of the G-Code file,
    we include the surrounding lines of G-Code in the representation when possible. 

    We tell the parent function to disregard the line if it is unlikely to uniquely identify
    the line of G-Code as otherwise we'll end up with too many false-positives when matching 
    between flavors

    Args:
        i (int): The index of the line in the lines list.
        lines (list): The list of lines.

    Returns:
        tuple: A tuple containing the line segment and a flag indicating whether to disregard the line segment.
    """
    line_1 = lines[i]
    if line_1 == ";END gcode for filament":
        return line_1, False
    if 'final' in line_1:
        return 'final', False
    line_2 = None
    if i + 1 < len(lines):
        line_2 = lines[i + 1]
    line_3 = None
    if i + 2 < len(lines):
        line_3 = lines[i + 2]

    line_1 = remove_nums(line_1)
    line_seg_1 = line_1.split(' E')[0]
    if 'E' in line_1:
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

def insert_first_delimiter(content_a, content_b):
    """
    Inserts the first delimiter in both of the G-Codes
    Note that this expects content_a to be Marlin and content_b to be Sailfish

    Args:
        content_a (str): The first content string.
        content_b (str): The second content string.

    Returns:
        tuple: A tuple containing the modified content strings.
            - content_a_before (str): The modified content_a before the delimiter.
            - content_a_after (str): The modified content_a after the delimiter.
            - content_b_before (str): The modified content_b before the delimiter.
            - content_b_after (str): The modified content_b after the delimiter.
    """
    content_a_before = content_a.split('G92 E0')[0] + 'G92 E0'
    content_a_after = 'G92 E0'.join(content_a.split('G92 E0')[1:])

    num_lines_a = len(content_a_before.split('\n'))
    content_b_before = content_b.split('\n')[:num_lines_a]
    content_b_after = content_b.split('\n')[num_lines_a:]

    content_b_before = '\n'.join(content_b_before)
    content_b_after = '\n'.join(content_b_after)
    return content_a_before, content_a_after, content_b_before, content_b_after

def insert_delimiters_F(content, debug=False):
    """
    Inserts delimiters in the given G-Code to separate different contours.

    Args:
        content (str): The input content to process.
        debug (bool, optional): Flag to enable debug mode. Defaults to False.

    Returns:
        str: The processed content with delimiters inserted.

    """
    content_lines = content.split('\n')
    output_content = []
    split_happened = False
    recent_split = True
    added_delim = False
    if content_lines[-1] == '':
        content_lines.pop()
    for i, line in enumerate(content_lines):
        if debug:
            print(line)
            # pdb.set_trace()
        if ('G1' in line and 'F' in line and not 'E' in line):
            if split_happened and not recent_split and i < len(content_lines) - 1:
                recent_split = True
                output_content.append('</del>')
                added_delim = True
            split_happened = True
            if added_delim:
                split_happened = False
                added_delim = False
        elif recent_split and 'G' in line and 'Y' in line and 'X' in line and 'E' in line:
            recent_split = False

        output_content.append(line)
    output_str = '\n'.join(output_content)
    return output_str

def make_hash_idx(blocks):
    """
    Creates a hash-based lookup table and identifies duplicate line segments.

    Args:
        blocks (list): A list of blocks containing line segments.

    Returns:
        tuple: A tuple containing the lookup table and a set of duplicate line segments.
            - lookup (dict): A dictionary where the keys are line segments and the values are the corresponding block indices.
            - duplicate_segs (set): A set of line segments that appear in multiple blocks.
    """
    lookup = {}
    duplicate_segs = set()
    for idx, block in enumerate(blocks):
        block_lines = block.strip().split('\n')
        for i in range(len(block_lines)):
            line_seg, disregard = make_line_seg(i, block_lines)
            if disregard:
                continue
            if line_seg in lookup and lookup[line_seg] != idx:
                duplicate_segs.add(line_seg)
                continue
            lookup[line_seg] = idx
    return lookup, duplicate_segs

def flip_layer_on_contours(layer_a, layer_b):
    """
    Rearranges the contours in layer_b to match the ordering of the contours in layer_a.
    This is done by defining a bijection between the contours in each layers which have 
    the same semantics and flipping the contours of layer_b to match the ordering of the
    contours in layer_a

    If a bijection cannot be found the contour flipping of this layer is marked as a failure

    Args:
        layer_a_plain (str): The plain text content of layer A.
        layer_b_plain (str): The plain text content of layer B.

    Returns:
        str: The full text content of layer_b after flipping 
    """
    # Sometimes the first delimiter isn't recognized so we just get rid of the stuff before it and then tack that part
    # back on at the end
    content_a_before, layer_a, content_b_before, layer_b = insert_first_delimiter(layer_a, layer_b)
    layer_a += '\n final'
    layer_b += '\n final'

    # we insert delimiters between all the contours to efficiently split the text into blocks
    # note that A and B should have same set of contours but in a different order
    layer_a_delimited = insert_delimiters_F(layer_a)
    layer_b_delimited = insert_delimiters_F(layer_b)
    layer_a_blocks = layer_a_delimited.strip().split('</del>\n')
    layer_b_blocks = layer_b_delimited.strip().split('</del>\n')

    #checking for degenerate conditions
    if len(layer_a_blocks) != len(layer_b_blocks):
        raise Exception('Different number of blocks')
    if len(layer_a_blocks) <= 1:
        return content_b_before + layer_b
    if layer_a_blocks[-1] == "":
        layer_a_blocks.pop()
    
    # Create hash index of blocks in layer_b
    lookup, duplicate_segs = make_hash_idx(layer_b_blocks)
    
    # Match blocks in layer_a to blocks in layer_b using hash index
    b_found = {}
    for idx_a, block_a in enumerate(layer_a_blocks):
        block_a_lines = block_a.strip().split('\n')
        found = False
        for i in range(len(block_a_lines)):
            line_seg, disregard = make_line_seg(i, block_a_lines)
            if disregard:
                continue
            if line_seg in lookup and line_seg not in duplicate_segs:
                idx_b = lookup[line_seg]
                if idx_b in b_found:
                    raise Exception('Not injective')
                b_found[idx_b] = (idx_a, line_seg)
                found = True
                break

        if not found:
            debug(layer_a, layer_b, layer_a_delimited, layer_b_delimited)
            leftover_a = layer_a_blocks[idx_a:]
            leftover_b = [layer_b_blocks[i] for i in range(len(layer_b_blocks)) if i not in b_found.keys()]
            raise Exception('Could not find a matching block')
    
    if len(b_found) < len(layer_b_blocks):
        raise Exception('Not surjective')
    
    flipped = [None for _ in range(len(layer_b_blocks))]
    for idx_b, (idx_a, line_seg) in b_found.items():
        flipped[idx_a] = layer_b_blocks[idx_b]
    
    flipped_text = ''.join(flipped)
    full_text = content_a_before + flipped_text
    
    return full_text

def flip_on_contours(text_a, text_b):
    """
    Flips the layers in text_b based on the contours in text_a.

    Args:
        text_a (str): The original G-code text containing the contours.
        text_b (str): The G-code text to be flipped based on the contours.

    Returns:
        tuple: A tuple containing the following elements:
            - output_a (str): text_a with the original contours.
            - output_b (str): The modified text_b with the flipped contours.
            - successes (int): The number of layers which were successfuly flipped.
            - failures (int): The number of layer which were unsuccessfuly flipped.
    """
    text_a_layers = text_a.strip().split(';LAYER_CHANGE')
    text_b_layers = text_b.strip().split(';LAYER_CHANGE')
    zipped_layers = zip(text_a_layers[1:], text_b_layers[1:])
    if not len(text_a_layers) == len(text_b_layers):
        return "","", 0, len(text_a_layers)
    assert len(text_a_layers) == len(text_b_layers)
    successes = 0
    failures = 0
    output_a_list = [text_a_layers[0]]
    output_b_lst = [text_b_layers[0]]
    for i, (layer_a, layer_b) in enumerate(zipped_layers):
        output_a_list.append(layer_a)
        try:
            flipped_layer_b = flip_layer_on_contours(layer_a, layer_b)
            output_b_lst.append(flipped_layer_b)
            successes += 1
        except Exception as e:
            failures += 1
            output_a_list.pop()
    output_a = ';LAYER_CHANGE'.join(output_a_list)
    output_b = ';LAYER_CHANGE'.join(output_b_lst)
    output_a = output_a.replace('\n final', '')
    output_b = output_b.replace('\n final', '')
    return output_a, output_b, successes, failures
