# Copyright 2023 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
# regular:
python examples/scripts/sft.py \
    --model_name_or_path="facebook/opt-350m" \
    --report_to="wandb" \
    --learning_rate=1.41e-5 \
    --per_device_train_batch_size=64 \
    --gradient_accumulation_steps=16 \
    --output_dir="sft_openassistant-guanaco" \
    --logging_steps=1 \
    --num_train_epochs=3 \
    --max_steps=-1 \
    --push_to_hub \
    --gradient_checkpointing \

# peft:
python examples/scripts/sft.py \
    --model_name_or_path="facebook/opt-350m" \
    --report_to="wandb" \
    --learning_rate=1.41e-5 \
    --per_device_train_batch_size=64 \
    --gradient_accumulation_steps=16 \
    --output_dir="sft_openassistant-guanaco" \
    --logging_steps=1 \
    --num_train_epochs=3 \
    --max_steps=-1 \
    --push_to_hub \
    --gradient_checkpointing \
    --use_peft \
    --lora_r=64 \
    --lora_alpha=16
"""
from dataclasses import dataclass, field

import torch
import json
import torch.utils.data as data
from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoTokenizer, HfArgumentParser, TrainingArguments

from trl import ModelConfig, SFTTrainer, get_kbit_device_map, get_peft_config, get_quantization_config
import random
import pdb
tqdm.pandas()
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import evaluate
import numpy as np
from datasets import Dataset,Features,Value
import pdb
torch.autograd.set_detect_anomaly(True)
import sys
import time 
import wandb

@dataclass
class ScriptArguments:
    dataset_name: str = field(default="timdettmers/openassistant-guanaco", metadata={"help": "the dataset name"})
    dataset_text_field: str = field(default="text", metadata={"help": "the text field of the dataset"})
    max_seq_length: int = field(default=512, metadata={"help": "The maximum sequence length for SFT Trainer"})

def data_name(name,keys):
    if name.lower() == "marlin":
        return "text_1"
    elif name.lower() == "sailfish":
        return "text_2"
    else:
        raise ValueError(f"Invalid flavor name: {name}")

class GcodeDataset(data.Dataset):
    def __init__(self, gcode_data_path,tokenizer,source,target):
        self.data = json.load(open(gcode_data_path, 'r'))
        # shuffle data
        random.seed(42)
        random.shuffle(self.data)
        self.size = len(self.data)
        print('dataset size:',self.size)
        sys.stdout.flush()
        self.tokenizer = tokenizer
        self.source = source
        self.target = target
        self.max_seq = 1024
        avg_len, max_len = self.get_stats()

    def __getitem__(self, index):
        source_name = data_name(self.source, self.data[index].keys())
        target_name = data_name(self.target, self.data[index].keys())

        source_text = self.data[index][source_name]
        target_text = self.data[index][target_name]

        text = f"Instruction: Translate the inputted GCode from {self.source} to {self.target} \n Input:{source_text} \n Output:{target_text} <|endoftext|>"

        tokenized = self.tokenizer(text, return_tensors="pt", padding="max_length", max_length=self.max_seq, truncation=True)
        tokenized["labels"] = tokenized.input_ids
        # assert tokenizer.eos_token_id in tokenized["labels"]
        return tokenized
    
    def __len__(self):
        return self.size
    
    def get_stats(self):
        # sample random indices
        indices = random.sample(range(self.size), min(100, self.size))
        total_len = 0
        max_len = 0
        max_idx = 0
        for i in indices:
            count = (self[i]["labels"][0] != 2).sum()
            total_len += count
            if count > max_len:
                max_len = count
                max_idx = i
        avg_len = total_len / len(indices)
        print(f"Average sequence length: {avg_len}")
        print(f"Maximum sequence length: {max_len}")
        print(f"Example with maximum length: {max_idx,self[max_idx]}")

        return avg_len, max_len

def compute_metrics(eval_preds):
    metric = evaluate.load("accuracy",training_args.output_dir.split('/')[-1])
    logits, labels = eval_preds
    predictions = np.argmax(logits,axis=-1)
    predictions = np.reshape(predictions.astype(np.int32),-1)
    labels = np.reshape(labels.astype(np.int32),-1)
    return metric.compute(predictions=predictions, references=labels)

if __name__ == "__main__":
    start_time = time.time()
    parser = HfArgumentParser((ScriptArguments, TrainingArguments, ModelConfig))
    parser.add_argument("--new_tokenizer", type=str, default=None, help="The tokenizer to use")
    parser.add_argument("--source", type=str, default="Marlin", help="The source flavor to use")
    parser.add_argument("--target", type=str, default="Sailfish", help="The target flavor to use")
    parser.add_argument("--job_id", type=str, default=None, help="The sbatch job id")
    parser.add_argument("--task_id", type=str, default=None, help="The sbatch task id")
    parser.add_argument("--notes", type=str, default="", help="The notes for wandb")
    args, training_args, model_config,other_args = parser.parse_args_into_dataclasses()
    dataset = args.dataset_name
    training_args.gradient_checkpointing_kwargs = dict(use_reentrant=False)
    
    #initialize wandb
    wandb_name = "interactive"
    if other_args.job_id is not None:
        wandb_name = other_args.job_id
    if other_args.task_id is not None:
        wandb_name = wandb_name + "_" + other_args.task_id

    wandb_config = {}
    wandb_config["dataset"] = dataset
    wandb_config["base_model"] = model_config.model_name_or_path

    tags = []
    wandb.init(project="gcode_peft", name=wandb_name, \
            config=wandb_config, notes=other_args.notes,tags=tags)
    ################
    # Model & Tokenizer
    ################
    torch_dtype = (
        model_config.torch_dtype
        if model_config.torch_dtype in ["auto", None]
        else getattr(torch, model_config.torch_dtype)
    )
    quantization_config = get_quantization_config(model_config)
    model_kwargs = dict(
        revision=model_config.model_revision,
        trust_remote_code=model_config.trust_remote_code,
        attn_implementation=model_config.attn_implementation,
        torch_dtype=torch_dtype,
        use_cache=False if training_args.gradient_checkpointing else True,
        device_map=get_kbit_device_map() if quantization_config is not None else None,
        quantization_config=quantization_config,
    )
    access_token = "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"
    tokenizer = AutoTokenizer.from_pretrained(model_config.model_name_or_path, token=access_token,use_fast=True, add_eos=True)
    tokenizer.pad_token = "#"
    ################
    # Dataset
    ################
    add_eos = lambda x: x + "<|endoftext|>"
    print('dataset name:',args.dataset_name)
    full_dataset = GcodeDataset(args.dataset_name,tokenizer,other_args.source,other_args.target)
    val_dataset_size = 150
    train_dataset_size = len(full_dataset) - val_dataset_size
    train_dataset, eval_dataset = data.random_split(full_dataset, [train_dataset_size, val_dataset_size] )
    print('len train dataset:',len(train_dataset))
    print('len eval dataset:',len(eval_dataset))
    training_args.save_steps = 100
    # training_args.fp16 = True
    print('model config:')
    print(model_config)
    print('training args')
    print(training_args)
    print('peft config:')
    print(get_peft_config(model_config))
    trainer = SFTTrainer(
        model=model_config.model_name_or_path,
        model_init_kwargs=model_kwargs,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        tokenizer=tokenizer,
        packing=False,
        peft_config=get_peft_config(model_config),
        compute_metrics=compute_metrics,
        dataset_num_proc=20)
    # pdb.set_trace()
    def format_time(t):
        return time.strftime("%H:%M:%S", time.gmtime(t))
    print('initial evaluation at time:',format_time(time.time()-start_time))
    trainer.evaluate()
    print('starting training at time:',format_time(time.time()-start_time))
    # pdb.set_trace()
    trainer.train()
    trainer.save_model(training_args.output_dir)