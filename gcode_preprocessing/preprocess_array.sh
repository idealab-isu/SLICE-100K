#!/bin/bash
#SBATCH --job-name=preprocess_gcode
#SBATCH --output=slurm/preprocess_gcode_array_%A_%a.out
#SBATCH --error=slurm/preprocess_gcode_array_%A_%a.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=km3888@nyu.edu
#SBATCH --time=36:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
#SBATCH --array=2-2

OVERLAY=/scratch/km3888/singularities/adapter/overlay-50G-10M.ext3:ro
SINGULARITY_IMAGE=/scratch/work/public/singularity/cuda11.8.86-cudnn8.7-devel-ubuntu22.04.2.sif 

# singularity exec --nv --overlay $OVERLAY $SINGULARITY_IMAGE /bin/bash -c " \
# source /ext3/env.sh; \
# python3 gcode_preprocessing/create_dataset.py --n_files 6000;"

# we want to run the above command with different arguments
# the two command line flags are --include_prev and --relative_extrusion
# we can use the array index to determine which flags to use

# if the array index is 0, we don't use either flag
# if the array index is 1, we use --include_prev
# if the array index is 2, we use --relative_extrusion
# if the array index is 3, we use both flags

# we can use an if statement to determine which flags to use
if [ $SLURM_ARRAY_TASK_ID -eq 0 ]; then
  FLAGS=""
elif [ $SLURM_ARRAY_TASK_ID -eq 1 ]; then
  FLAGS="--include_prev"
elif [ $SLURM_ARRAY_TASK_ID -eq 2 ]; then
  FLAGS="--relative_extrusion"
elif [ $SLURM_ARRAY_TASK_ID -eq 3 ]; then
  FLAGS="--include_prev --relative_extrusion"
fi

singularity exec --nv --overlay $OVERLAY $SINGULARITY_IMAGE /bin/bash -c " \
source /ext3/env.sh; \
python3 gcode_preprocessing/create_dataset.py --n_files 6000 $FLAGS;"

# we can now submit this script to the cluster