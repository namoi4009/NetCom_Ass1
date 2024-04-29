import bencodepy
import re
from collections import OrderedDict
# try:
#     import psyco # Optional, 2.5x improvement in speed
#     psyco.full()
# except ImportError:
#     pass
decimal_match = re.compile('\d')

def bencode(value):
    return bencodepy.encode(value).decode()

def bdecode(data):
    '''Main function to decode bencoded data'''
    chunks = list(data)
    chunks.reverse()
    root = _dechunk(chunks)
    return root

def _dechunk(chunks):
    item = chunks.pop()

    if item == 'd': 
        item = chunks.pop()
        hash = {}
        while item != 'e':
            chunks.append(item)
            key = _dechunk(chunks)
            hash[key] = _dechunk(chunks)
            item = chunks.pop()
        return hash
    elif item == 'l':
        item = chunks.pop()
        list = []
        while item != 'e':
            chunks.append(item)
            list.append(_dechunk(chunks))
            item = chunks.pop()
        return list
    elif item == 'i':
        item = chunks.pop()
        num = ''
        while item != 'e':
            num  += item
            item = chunks.pop()
        return int(num)
    elif decimal_match.search(item):
        num = ''
        while decimal_match.search(item):
            num += item
            item = chunks.pop()
        line = ''
        for i in range(int(num)):
            line += chunks.pop()
        return line
    raise "Invalid input!"




# a=10
# b="hello"
# c=[1,"hello",3]
# d={"a":1,"b":[{"b1.1":3,"b1.2":"hello"},{"b2.1":4,"b2.2":"world"}]}

# bencoded_a=bencode(a)
# bencoded_b=bencode(b)
# bencoded_c=bencode(c)
# bencoded_d=bencode(d)
# print(bencoded_a)
# print(bencoded_b)
# print(bencoded_c)
# print(bencoded_d)
# print("=================")
# bdecoded_bencoded_a=bdecode(bencoded_a)
# bdecoded_bencoded_b=bdecode(bencoded_b)
# bdecoded_bencoded_c=bdecode(bencoded_c)
# bdecoded_bencoded_d=bdecode(bencoded_d)
# print(bdecoded_bencoded_a)
# print(bdecoded_bencoded_b)
# print(bdecoded_bencoded_c)
# print(bdecoded_bencoded_d)
# print("=================")
# print(a==bdecoded_bencoded_a)
# print(b==bdecoded_bencoded_b)
# print(c==bdecoded_bencoded_c)
# print(d==bdecoded_bencoded_d)





