import json
import pdb
import numpy as np
from transformers import AutoTokenizer
#load tokenizer
model_name = 'bigcode/starcoder'


tokenizer = AutoTokenizer.from_pretrained(model_name,use_fast=True)
tokenizer.pad_token = tokenizer.eos_token
json_path = "/vast/km3888/paired_gcode/layer_data_100.json"
with open(json_path,'r') as f:
    json_out = json.load(f)

texts = [j['text'] for j in json_out]
lengths = [len(t) for t in texts]
lengths_np = np.array(lengths)
length_hist = np.histogram(lengths_np,bins=20)
max_len = max(lengths)

# find the longest text in terms of tokens
tokenized_texts = tokenizer(texts,return_tensors='pt',padding='max_length',max_length=max_len,truncation=True)
token_lengths = tokenized_texts['input_ids'].shape[1]
token_hist = np.histogram(token_lengths,bins=20)
max_token_len = max(token_lengths)
pdb.set_trace()