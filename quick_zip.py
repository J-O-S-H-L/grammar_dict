import os
import zipfile

def zip_directory(directory_path, zip_name):
    with zipfile.ZipFile(f"{zip_name}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(directory_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                zipf.write(file_path, os.path.relpath(file_path, directory_path))

if __name__ == "__main__":
    directory_path = r"test_dict" 
    zip_name = "bunpro_dict"
    zip_directory(directory_path, zip_name)
