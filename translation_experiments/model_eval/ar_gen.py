import json 
from transformers import pipeline,AutoTokenizer
import pdb 
from transformers import GPT2Tokenizer, GPT2LMHeadModel, GenerationConfig, AutoModelForCausalLM
import prettytable
import argparse
import os
from transformers import LogitsProcessor, StoppingCriteria, StoppingCriteriaList
import torch
from peft import PeftModel, PeftConfig

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

def fixed_length_chunking(text,chunk_size):
    layer_split = text.split('\n')
    layer_split = [x for x in layer_split if len(x)]
    chunked_text = []
    for i in range(0,len(layer_split),chunk_size):
        chunk = layer_split[i:i+chunk_size]
        # chunk = [x for x in chunk if len(x)]
        chunked_text.append("\n".join(chunk)+"\n")
    return chunked_text

def get_model(model_name,is_peft=False):
    # Load your model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name,use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token 

    if is_peft:
        peft_config = PeftConfig.from_pretrained(model_name)
        base_model = AutoModelForCausalLM.from_pretrained(peft_config.base_model_name_or_path)
        model = PeftModel(base_model,peft_config)
    else:
        if "llama" in model_name:
            model = AutoModelForCausalLM.from_pretrained(model_name,local_files_only=True,return_dict=True).to("cuda:0")
        else:
            model = GPT2LMHeadModel.from_pretrained(model_name).to("cuda:0")
    return model,tokenizer

def generate_text(model,tokenizer,starting_text):
    # Your input text (the first half of a text)
    assert model.device!="cpu"
    text_ids = tokenizer.encode(starting_text,return_tensors='pt').to(model.device)
    gen_config = GenerationConfig()
    gen_config.pad_token_id = 2
    # gen_config.eos_token_id = tokenizer.eos_token_id
    # Generate a sequence of text
    stopping_criteria_eos = EOSStoppingCriteria(tokenizer.eos_token_id)
    stopping_criteria = StoppingCriteriaList([stopping_criteria_eos])
    output = model.generate(text_ids, generation_config=gen_config, num_return_sequences=1, \
        temperature=0.7,output_scores=True,stopping_criteria=stopping_criteria, length_penalty=-1.0, \
        return_dict_in_generate=True,max_length=700,do_sample=True,num_beams=5,top_k=5)
    # print('gen length:',output[0].shape[1])
    # # Decode the generated text
    # predicted_logits = model(output[0]).logits
    # pred_maxes = predicted_logits.max(dim=-1)[0]
    # pred_eos = predicted_logits[:,:,-1]
    # eos_diff = pred_maxes - pred_eos
    # print('eos diff max:',eos_diff.min())
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

def one_layer_comparison(model_path,layer,model=None,tokenizer=None):
    if model is None or tokenizer is None:
        print('loading model...')
        model,tokenizer = get_model(model_path)
    # model,tokenizer = get_model(model_path)
    layer_split = fixed_length_chunking(layer,20)
    output_layer = []
    for chunk in layer_split:
        starting_text = "Instruction: Translate the inputted GCode from Marlin to Sailfish \n Input: %s \n Output:" % chunk
        output = generate_text(model,tokenizer,starting_text)
        if isinstance(output,tuple):
            output = output[0]
        output_layer.append(output)
    output_layer = "".join(output_layer)
    # with open(f'output_{args.model_path}.txt','a') as f:
    #     f.write(str(table))
    #     f.write('\n')
    return layer, output_layer
    