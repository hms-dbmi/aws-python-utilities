import base64



def read_settings_file(filename):
    d = {}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                (key, val) = line.split("=", 1)
                d[key] = val
    return d


def read_key_file(filename):
    with open(filename, "rb") as key_file:
        encoded_string = base64.b64encode(key_file.read())

    return encoded_string
