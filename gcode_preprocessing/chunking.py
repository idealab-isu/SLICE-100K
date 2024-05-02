import pdb
from preprocess_utils import debug

def chunk_debug(text_a_lines, text_b_lines, start_i, end_i, start_j, end_j, max_lines):
    """
    Debugs the chunking process by highlighting the start and end lines in the given text_a_lines and text_b_lines.

    Args:
        text_a_lines (list): List of lines from text A.
        text_b_lines (list): List of lines from text B.
        start_i (int): Start index of the chunk in text_a_lines.
        end_i (int): End index of the chunk in text_a_lines.
        start_j (int): Start index of the chunk in text_b_lines.
        end_j (int): End index of the chunk in text_b_lines.
        max_lines (int): Maximum number of lines to include in the debug output.

    Returns:
        None
    """
    if end_j == -1:
        end_j = start_j + max_lines + 1
    debug_a_lines = text_a_lines[:start_i + max_lines + 1]
    debug_b_lines = text_b_lines[:end_j + 1]

    debug_a_lines[start_i] += " START"
    debug_a_lines[end_i] += " END"

    debug_b_lines[start_j] += " START"
    debug_b_lines[end_j] += " END"

    debug_a = "\n".join(debug_a_lines)
    debug_b = "\n".join(debug_b_lines)

    debug(debug_a, debug_b)

def find_same(text_a_lines,text_b_lines,i,start_j,max_lines):
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
    # pdb.set_trace()
    line_i = text_a_lines[i]
    if 'G92 E0' in line_i:
        return -1
    line_i = line_i.split(' E')[0]
    permitted = [';TYPE:Overhang perimeter', ';LAYER_CHANGE',";TYPE:External perimeter"]
    for j,line in enumerate(text_b_lines[start_j:start_j+2*max_lines]):
        if not "X" in line or not "Y" in line:
            if line not in permitted and ";WIDTH" not in line:
                continue
        #make sure that we're looking at a coordinate placement line
        #remove the extrusion value since that varies across flavors
        line_j = line.split(' E')[0]
        if line_j==line_i:
            return j+start_j
    return -1

def aligned_chunks(text_a, text_b, max_lines):
    """
    Generate corresponding chunks of bounded length given two G-code files.
    Each pair of chunks is "aligned" meaning that all the 3D information present in one
    chunk is also present in the other chunk as they both describe the same parts of the
    shape. 

    Note: This function assumes that the two G-code files are already aligned at the
    contour level, meaning that each G-code instructs the 3D printer to move from one
    contour to the next in the same order. 

    Args:
        text_a (str): G-code file in flavor A (e.g Marlin)
        text_b (str): G-code file in flavor B (.eg Sailfish)
        max_lines (int): The maximum number of lines in each chunk.

    Returns:
        list: A list of dictionaries, where each dictionary represents an aligned chunk.
              Each dictionary contains two keys: 'text_1' for the chunk of text_a and
              'text_2' for the chunk of text_b.
    """
    if not len(text_a) or not len(text_b):
        return []
    if not (isinstance(text_a, str) and isinstance(text_b, str)):
        pdb.set_trace()
    text_a_lines = text_a.strip().split('\n')
    text_b_lines = text_b.strip().split('\n')
    debug(text_a, text_b)
    num_lines = len(text_a_lines)
    start_i = 0
    end_i = min(start_i + max_lines, num_lines)
    start_j = 0
    chunks = []
    while start_i < num_lines:
        if num_lines - start_i <= max_lines:
            chunk_a = "".join(x + "\n" for x in text_a_lines[start_i:])
            chunk_b = "".join(x + "\n" for x in text_b_lines[start_j:])
            chunks.append({"text_1": chunk_a, "text_2": chunk_b})
            break
        end_j = find_same(text_a_lines, text_b_lines, end_i, start_j, max_lines)
        if (end_j - start_j) > 2 * (end_i - start_i):
            raise Exception("Something bad happened")
        if end_j != -1 and ((end_j - start_j) * 2 < (end_i - start_i)):
            # check whether text_a_lines[i] is a duplicate within its own chunk
            text_a_chunk = text_a_lines[start_i:end_i]
            text_a_chunk_no_e = [x.split(' E')[0] for x in text_a_chunk]
            if text_a_lines[end_i].split(' E')[0] in text_a_chunk_no_e:
                end_i -= 1
                continue
            else:
                raise Exception("Something bad happened")
        if end_j == -1:
            if (end_i - start_i) < max_lines // 2:
                raise Exception("Hey what's going on here")
            end_i -= 1
        else:
            chunk_b = "".join(x + "\n" for x in text_b_lines[start_j:end_j + 1])
            chunk_a = "".join(x + "\n" for x in text_a_lines[start_i:end_i + 1])
            chunks.append({"text_1": chunk_a, "text_2": chunk_b})
            start_i = end_i + 1
            start_j = end_j + 1
            end_i = min(start_i + max_lines, num_lines)

    return chunks