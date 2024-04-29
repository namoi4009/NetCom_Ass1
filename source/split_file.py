import os 

MEM="Chunks"
SIZE=1024*512

def split_file(file_name):
    memory_dir=MEM
    chunk_size=SIZE 
    # Open the file for reading in binary mode
    with open(os.path.join(memory_dir, file_name), 'rb') as file:
        chunk_number = 1
        while True:
            # Read a chunk of data
            chunk_data = file.read(chunk_size)
            if not chunk_data:
                break  # No more data to read
            
            # Create a filename for the chunk
            chunk_filename = f"{memory_dir}/{os.path.basename(file_name)}.part{chunk_number}"
            
            # Write the chunk data to the chunk file
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            
            chunk_number += 1

if __name__ == "__main__":
    split_file("Original_Files/file1.webm")
    split_file("Original_Files/file2.webm")