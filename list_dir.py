# Generates an indented and a compact directory tree,
# excluding (node_modules, venv, .git) contents, and saves to a timestamped text file.

import os
import datetime

def print_directory_tree(root_dir, exclude_dirs=None, output_file=None, prefix=""):
    if exclude_dirs is None:
        exclude_dirs = ["node_modules", "venv", ".git"]
    if not os.path.isdir(root_dir):
        return

    dir_contents = sorted(os.listdir(root_dir), key=lambda x: (os.path.isfile(os.path.join(root_dir, x)), x))

    for path in dir_contents:
        full_path = os.path.join(root_dir, path)
        if os.path.isdir(full_path):
            output_file.write(prefix + path + "/\n")
            if path not in exclude_dirs:
                print_directory_tree(full_path, exclude_dirs, output_file, prefix=prefix + "    ")
        else:
            output_file.write(prefix + path + "\n")

def print_compact_directory_tree(root_dir, base_dir, exclude_dirs=None, output_file=None):
    if exclude_dirs is None:
        exclude_dirs = ["node_modules", "venv", ".git"]
    if not os.path.isdir(root_dir):
        return

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for name in dirs:
            output_file.write(os.path.relpath(os.path.join(root, name), base_dir) + "/\n")
        for name in files:
            output_file.write(os.path.relpath(os.path.join(root, name), base_dir) + "\n")

def list_directories(root_dir, output_file):
    output_file.write("Full directory tree with indentation:\n")
    print_directory_tree(root_dir, output_file=output_file)
    
    output_file.write("\nFull directory tree without indentation:\n")
    print_compact_directory_tree(root_dir, root_dir, output_file=output_file)

# Start directory
start_dir = "C:\\Users\\astab\\Desktop\\Coding\\PROGECT"

# Create a unique filename with a timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"directory_tree_{timestamp}.txt"

# Open the file for writing
with open(output_filename, "w") as output_file:
    list_directories(start_dir, output_file)

print(f"Directory tree has been saved to {output_filename}")
