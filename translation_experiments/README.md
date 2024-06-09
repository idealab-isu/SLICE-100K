# GCode Translation

All the code need to reproduce the experiments section of our paper, starting with the preprocessing followed by the training and evaluation code for the translation models.


## Installation

Create a new environment and run:

```pip install -r requirements.txt```


## Preprocessing

To do all the preprocessing (extrusion conversion, contour flipping, and pair creation) simply run the following:

```
export PYTHONPATH=$(pwd):$PYTHONPATH
python3 gcode_preprocessing/create_dataset.py --chunk_size [NUM_CHUNKS] --n_files [NUM_FILES] --data_path [PATH_TO_UNPROCESSED G-CODE]--output_path [OUTPUT_PATH] --relative_extrusion
```


## Model Training
To train a translation model on your preprocessed data you can then do:
```
export PYTHONPATH=$(pwd):$PYTHONPATH
python model_training/sft.py \
    --model_name_or_path=[BASE_MODEL_PATH] \
    --report_to="wandb" \ # optional
    --learning_rate=1.41e-5 \
    --per_device_train_batch_size=12 \ #adjust as needed
    --per_device_eval_batch_size=4 \
    --gradient_accumulation_steps=16 \
    --output_dir=[LOG DiRECTORY] \
    --logging_steps=1 \
    --num_train_epochs=6 \
    --max_seq_length=1024 \
    --max_steps=20000 \
    --evaluation_strategy="steps" \
    --eval_steps=200 \
    --eval_accumulation_steps=2 \
    --dataset_name [DATASET_PATH] \
    --gradient_checkpointing \
    --source 'Sailfish' \
    --target 'Marlin' \
    --use_peft \ #optional (not used in paper experiments)
```


## Model Evaluation

Finally, model eval can be done with the following command which will save all the results to EVAL_LOGGING_DIRECTORY

```
export PYTHONPATH=$(pwd):$PYTHONPATH
python model_eval/eval_model.py \
    --model_path [TRAINED_MODEL] \
    --base_data_dir [ORIGINAL_DATA_DIRECTORY]
    --output_base_dir [EVAL_LOGGING_DIRECTORY]
```