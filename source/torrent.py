from bencode import bencode,bdecode
class TorrentFile:
        def __init__(self,
                announce="",                                    # The announce URL of the tracker (string)
                info = {                                        # a dictionary that describes the file(s) of the torrent.
                        "name":"movie",                         # the name of the directory in which to store all the files.      
                        "piece_length":512*1024,                        # number of bytes in each piece (integer) 
                        "pieces":"dvbsdsfsd",                           # string consisting of the concatenation of all 20-byte SHA1 hash values, one per piece (byte string, i.e. not urlencoded)
                        "files":[                                       #multi-file module
                                {"length":1*1024*1024,                          # length of the file in bytes (integer)
                                "path":["folder0","folder1","abc.mp4"]},        # a list containing one or more string elements that together represent the path and filename.
                                {"length":512*1024,
                                "path":["folder2","folder3","xyz.mp4"]},
                                {"length":2*1024*1024,
                                "path":["folder0","folder1","temp","pokemon.mp4"]}]
                        }
                ):
                self.announce = announce
                self.info = info
        def bencode_TorrentFile(self):
                return bencode(self.announce)+bencode(self.info)
        def bdecode_TorrentFile(self,bencoded_msg):
                str_i=0
                str_num=""
                while(bencoded_msg[str_i]!=":"):
                        str_num+=bencoded_msg[str_i]
                        str_i+=1
                index=int(str_num)+3
                self.announce = bdecode(bencoded_msg[:index])
                self.info = bdecode(bencoded_msg[index:])

# test1=TorrentFile(announce="trackerabc.com")
# test2=TorrentFile()
# temp=test1.bencode_TorrentFile()
# print("=========================")
# print(temp)
# print("=========================")
# print(test2.bencode_TorrentFile())
# print("=========================")
# test2.bdecode_TorrentFile(temp)#######################
# print(test2.bencode_TorrentFile())

