import bencodepy

def create_torrent_file(file_path, tracker_url):
    with open(file_path, 'rb') as f:
        file_contents = f.read()
    file_info = {
        'name': os.path.basename(file_path),
        'length': len(file_contents),
        'piece length': 512 * 1024,  # 512 KB per piece
        'pieces': [file_contents[i:i+512*1024] for i in range(0, len(file_contents), 512*1024)]
    }
    torrent_info = {
        'announce': tracker_url,
        'info': file_info
    }
    with open(file_path + '.torrent', 'wb') as f:
        f.write(bencodepy.encode(torrent_info))