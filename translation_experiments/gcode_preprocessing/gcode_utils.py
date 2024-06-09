import os
import shutil
import subprocess


# use this to move .gcode files from the .bgcode directory to a directory of your choice
def move_gcode_files(source_dir, destination_dir):
    # Create destination directory if it doesn't exist
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    
    # Loop through all files in the source directory
    for file in os.listdir(source_dir):
        if file.endswith('.gcode'):
            # Construct full file paths
            source_file = os.path.join(source_dir, file)
            destination_file = os.path.join(destination_dir, file)

            # Move the file
            shutil.move(source_file, destination_file)
            print(f"Moved {file} to {destination_dir}")



def binary_to_ascii(converter_path, gcode_path):

    command = [converter_path, gcode_path]
    result = subprocess.run(command, text=True, capture_output=True)

    if result.returncode == 0:
        print(result.stdout)
        return None
    else:
        print(f"Error converting from .bgcode to .gcode: {result.stderr}")
        return gcode_path
    
def convert_multiple_files(input_dir, converter_path):
    error_files = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.bgcode'):
            binary_file = os.path.join(input_dir, filename)
            print('binary_gcode_file: ', binary_file)
            error_file = binary_to_ascii(converter_path, binary_file)
            if error_file is not None:
                error_files.append(error_file)
    if len(error_files) > 0:
        print("Error converting the following files: ")
        for error_file in error_files:
            print(error_file)
    else:
        print("All files converted successfully!")

if __name__ == "__main__":
    
    input_dir = "/work/mech-ai-scratch/ajignasu/Objaverse/gcode/thingiverse_mini_binary/" # edit this to point to your local path of binary gcode directory
    converter_path = "/work/mech-ai/jignasu/LLM_Gcode/libbgcode/my_build/bin/bgcode" # edit this to point to your local path to bgcode

    convert_multiple_files(input_dir, converter_path)

    # move_gcode_files("path to directory with binary gcode", "path to where you want to move .gcode file")