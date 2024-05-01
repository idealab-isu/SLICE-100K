#!/bin/bash


OVERLAY=/scratch/km3888/singularities/adapter/overlay-50G-10M.ext3:ro
SINGULARITY_IMAGE=/scratch/work/public/singularity/cuda11.8.86-cudnn8.7-devel-ubuntu22.04.2.sif 

singularity exec --nv --overlay $OVERLAY $SINGULARITY_IMAGE /bin/bash -c " \
source /ext3/env.sh; \
python3 gcode_preprocessing/align_gcode.py \
"