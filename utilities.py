def read_settings_file(filename):
    d = {}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                (key, val) = line.split("=", 1)
                d[key] = val
    return d
