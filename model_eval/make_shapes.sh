#!/bin/bash

OVERLAY=/scratch/km3888/singularities/adapter/overlay-50G-10M.ext3:ro
IMAGE=/scratch/work/public/singularity/cuda11.8.86-cudnn8.7-devel-ubuntu22.04.2.sif

export HF_TOKEN="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"
export HF_DATASETS_CACHE="/scratch/km3888/hf_datasets"
export TRANSFORMERS_CACHE="/scratch/km3888/huggingface"

cd ~/gcode_processing
#add parent directory of current working directory to PYTHONPATH
MODEL_PATHS=("/scratch/km3888/gcode_peft/45337768_0/checkpoint-4000" "/scratch/km3888/gcode_peft/45337768_1/checkpoint-4000")
singularity exec --nv --overlay $OVERLAY $IMAGE /bin/bash -c "source /ext3/env.sh; \
    export PYTHONPATH=$PYTHONPATH:$(pwd); \
    python model_eval/make_shapes.py \
    --model_path /scratch/km3888/gcode_peft/46566087_1/checkpoint-100/ \
    --num_shapes 1 \
    --output_base_dir /vast/km3888/translation_evals \
    "


# MODEL_PATHS=("/scratch/km3888/gcode_peft/45337768_0/checkpoint-4000" "/scratch/km3888/gcode_peft/45337768_1/checkpoint-4000")
# singularity exec --nv --overlay $OVERLAY $IMAGE /bin/bash -c "source /ext3/env.sh; \
# python model_eval/eval_model.py"