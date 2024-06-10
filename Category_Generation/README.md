# Category Generation

All the code needed to generate the categories of the STL files using 10 renderings of each STL file


## Installation

Create a new environment and run:

```pip install -r requirements.txt```

Activate the environment

## Generating Categories

The code uses the renderings stored in the zipped folders contained in the parent folder. Folder Structure of the data

Parent Folder
│
├── Zipped_STL_Folder_1.zip
│
├── Zipped_STL_Folder_2.zip
│
└── ...

It unzips each folder, generate the category using the renderings stored in the folder and saves the categories in json file and zips the folder back

## Run the following command
python Category_Generation.py /path/to/parent_folder



