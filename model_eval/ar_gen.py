import json 
from transformers import pipeline,AutoTokenizer
import pdb 
from transformers import GPT2Tokenizer, GPT2LMHeadModel, GenerationConfig
import prettytable
import argparse
import os
from make_json_nlines import merge_list
from transformers import LogitsProcessor, StoppingCriteria, StoppingCriteriaList
import torch

class EOSStoppingCriteria(LogitsProcessor):
    def __init__(self, eos_token_id):
        self.eos_token_id = eos_token_id
        self.max_length = 400

    def __call__(self, input_ids, scores):
        if torch.any(input_ids[:,-1] == self.eos_token_id):
            return True
        if len(input_ids) >= self.max_length:
            return True
        return False
    
    def __len__(self):
        return 1


def get_model(model_name):
    # Load your model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name,use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token 
    model = GPT2LMHeadModel.from_pretrained(model_name)
    return model,tokenizer

def generate_text(model,tokenizer,starting_text):
    # Your input text (the first half of a text)
    text_ids = tokenizer.encode(starting_text,return_tensors='pt')
    gen_config = GenerationConfig()
    gen_config.pad_token_id = 2
    # gen_config.eos_token_id = tokenizer.eos_token_id
    # Generate a sequence of text
    stopping_criteria_eos = EOSStoppingCriteria(tokenizer.eos_token_id)
    stopping_criteria = StoppingCriteriaList([stopping_criteria_eos])
    output = model.generate(text_ids, generation_config=gen_config, num_return_sequences=5, \
        temperature=0.7,output_scores=True,stopping_criteria=stopping_criteria, length_penalty=-1.0, \
        return_dict_in_generate=True,max_length=1023,do_sample=True,num_beams=5,top_k=5)
    # print('gen length:',output[0].shape[1])
    # # Decode the generated text
    # predicted_logits = model(output[0]).logits
    # pred_maxes = predicted_logits.max(dim=-1)[0]
    # pred_eos = predicted_logits[:,:,-1]
    # eos_diff = pred_maxes - pred_eos
    # print('eos diff max:',eos_diff.min())
    # pdb.set_trace()
    generated_text = tokenizer.decode(output[0][-1].tolist(), skip_special_tokens=True)
    # Strip the instructions and input text from the generated code
    starting_gcode = starting_text.strip("Instruction: Translate the inputted GCode from Marlin to Sailfish and stop after one line \n ").strip(" \n Output: \n")
    # num_lines = len(starting_gcode.split('\n'))
    generated_gcode = generated_text.split(' \n Output:')[1]
    return generated_gcode, starting_gcode

def create_table(text1,text2):
    table = prettytable.PrettyTable()
    table.field_names = ["Input GCode", "Generated GCode"]
    table.add_row([text1, text2])
    print("Translation results:")
    print(table)
    return table

def list_to_string(lst):
    return '[' + '|'.join(lst) + ']'

def print_tokens(starting_gcode,generated_gcode):
    starting_tokens = tokenizer.encode(starting_gcode,return_tensors='pt')
    generated_tokens = tokenizer.encode(generated_gcode,return_tensors='pt')
    starting_tokens = [tokenizer.decode(t, skip_special_tokens=False) for t in starting_tokens[0]]
    generated_tokens = [tokenizer.decode(t, skip_special_tokens=False) for t in generated_tokens[0]]

    starting_token_str = list_to_string(starting_tokens)
    generated_token_str = list_to_string(generated_tokens)

    table_tokens = prettytable.PrettyTable()
    table_tokens.field_names = ["Input Tokens", "Generated Tokens"]
    table.add_row([starting_token_str, generated_token_str])
    print("Tokens")
    print(table_tokens)
    return table_tokens

def one_line_comparison(args):
    model,tokenizer = get_model(args.model_path)
    starting_text = "Instruction: Translate the inputted GCode from Marlin to Sailfish \n Input: G1 X69.026 Y59.001 E10.45398 \n Output: \n"
    generated_gcode, start_gcode = generate_text(model,tokenizer,starting_text)
    table = create_table(start_gcode,generated_gcode)
    with open(args.out_file,'a') as f:
        f.write(str(table))
        f.write('\n')
    print_tokens(start_gcode,generated_gcode)

def get_layer():
    data_dir = "/vast/km3888/paired_gcode/thingiverse_10k_marlin"    
    data_path = os.listdir(data_dir)[-1]
    data_path = os.path.join(data_dir,data_path)
    g_code_file = open(data_path,'r').read()
    layer = g_code_file.split(';LAYER_CHANGE')[1]
    return layer

def one_layer_comparison(args):
    model,tokenizer = get_model(args.model_path)
    layer = get_layer()
    layer_split = layer.split('\n')
    layer_split = [x + "\n" for x in layer_split[:-2]]+[layer_split[-1]]
    layer_split = merge_list(layer_split,10)
    output_layer = []
    print(f"{len(layer_split)} chunks")
    for chunk in layer_split:
        starting_text = "Instruction: Translate the inputted GCode from Marlin to Sailfish \n Input: %s \n Output:" % chunk
        output = generate_text(model,tokenizer,starting_text)
        if isinstance(output,tuple):
            output = output[0]
        output_layer.append(output)
    pdb.set_trace()
    output_layer = "".join(output_layer)
    with open(f"{args.experiment_id}_output.gcode",'w') as f:
        f.write(output_layer)
        f.write('\n')
    with open(f"{args.experiment_id}_input.gcode",'w') as f:
        f.write(layer)
        f.write('\n')
    # with open(f'output_{args.model_path}.txt','a') as f:
    #     f.write(str(table))
    #     f.write('\n')

    pdb.set_trace()
    
def test_on_train_input(args):
    model,tokenizer = get_model(args.model_path)
    data_file = "translation_data_100_instruct_20.json"
    data_path = "/vast/km3888/paired_gcode/%s" % data_file

    with open(data_path,'r') as f:
        data = json.load(f)
    for i in range(25):
        train_datapoint = data[i]
        full_text = train_datapoint['text']
        text_ids = tokenizer.encode(full_text+"<endoftext>",return_tensors='pt') # adding a pad token so we can predict next token
        model_preds = model(text_ids).logits
        eos_probs = torch.softmax(model_preds,dim=-1)[:,:,-1]
        # print(eos_probs.squeeze()[-1])
        print(eos_probs.max())

if __name__=="__main__":

    parser = argparse.ArgumentParser()
    # parser.add_argument('--model_path',default="/scratch/km3888/gcode_peft/checkpoint-8000",type=str)
    # parser.add_argument('--model_path',default="/scratch/km3888/gcode_peft/45428360_1/checkpoint-4500",type=str)
    # parser.add_argument('--model_path',default="openai-community/gpt2",type=str)
    # parser.add_argument('--model_path',default="/scratch/km3888/gcode_peft/45497828_0/checkpoint_500",type=str)
    parser.add_argument('--model_path',default="/scratch/km3888/gcode_peft/45516626_1/checkpoint-1000",type=str)

    args = parser.parse_args()
    experiment_id = args.model_path.split('/')[-2]
    args.experiment_id = experiment_id
    args.out_file = f'output_{experiment_id}.txt'
    # one_line_comparison(args)
    one_layer_comparison(args)
    # test_on_train_input(args)