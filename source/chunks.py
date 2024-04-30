import os

SIZE = 524288


def chunk(file_name):
    original = "Original_Files"
    desti = "Chunks"
    chunk_size = SIZE

    with open(os.path.join(original, file_name), 'rb') as file:
        chunk_number = 1
        while True:
            chunk_data = file.read(chunk_size)
            if not chunk_data:
                break

            chunk_filename = f"{desti}/{os.path.basename(file_name)}.part{chunk_number}"

            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk_data)

            chunk_number += 1


if __name__ == "__main__":
    chunk("mv1.mp4")
    chunk("mv2.mp4")
