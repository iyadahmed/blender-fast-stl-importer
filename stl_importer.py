import struct

with open("./suzanne_ascii.stl", "rb") as f:
    first_5_bytes = f.read(5)
    if first_5_bytes == b"solid":
        # ASCII STL
        name = f.readline().decode().strip()
        for line in f.readlines():
            print(line)

    else:
        # Binary STL
        f.read(80 - 5)  # consume rest of 80 bytes header
        num_tri = struct.unpack("<I", f.read(4))[0]
        for i in range(num_tri):
            pass
