import os
import json

# Load existing torrent file data
# torrent_file_path = r'C:\Users\ASUS\Desktop\HK232\MMT\BTL\BitTorrent\CN_Asignment1\src\Memory\torrent_file.json'  # Update with your torrent file path
# with open(torrent_file_path, 'r') as file:
#     torrent_data = json.load(file)

# Specify the directory where the chunks are located
chunk_directory = r'Memory'

# # Get the list of chunk filenames in the directory
# chunk_filenames = [filename for filename in os.listdir(chunk_directory) if filename.endswith('.part')]
#
# # Determine the starting index for the remaining chunks
# starting_index = len(torrent_data[0]['index']) + 1
#
# # Generate new chunk filenames for the remaining chunks
# remaining_chunk_filenames = [f"File_split.mp4.part{i}" for i in range(starting_index, starting_index + 69)]
#
# # Add the new chunk filenames to the index list in the torrent data
# torrent_data[0]['index'] += remaining_chunk_filenames
#
# # Write the updated torrent data back to the torrent file
# with open(torrent_file_path, 'w') as file:
#     json.dump(torrent_data, file, indent=4)
#
# print("Labels added to the remaining 69 chunks in the torrent file.")
