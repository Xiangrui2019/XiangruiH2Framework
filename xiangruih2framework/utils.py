def decodeurlencoding(string):
    string = string.replace('%', '')
    string = bytes.fromhex(string)
    return string.decode('utf-8')