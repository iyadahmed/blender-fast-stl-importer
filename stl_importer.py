import struct

normals = []
verts = []


def max_abs_diff(a, b):
    return max(map(abs, (a[0] - b[0], a[1] - b[1], a[2] - b[2])))


# Assuming all polys are tris
with open("./suzanne_ascii.stl", "rb") as f:
    first_5_bytes = f.read(5)
    if first_5_bytes == b"solid":
        # ASCII STL
        name = f.readline().decode().strip()
        for line in f.readlines():
            stripped_line = line.strip()
            if stripped_line.startswith(b"facet"):
                normal_str = stripped_line.rsplit(b" ", 3)[-3:]
                normal = [float(s) for s in normal_str]
                normals.append(normal)
            elif stripped_line.startswith(b"vertex"):
                vertex_str = stripped_line.rsplit(b" ", 3)[-3:]
                verts.append([float(s) for s in vertex_str])

        num_verts_non_unique = len(verts)
        faces = list(range(num_verts_non_unique))
        sorted_verts = sorted(zip(verts, faces), key=lambda item: item[0])

        # reduce verts to unique verts
        unique_verts = []
        current_unique_vert = None
        current_unqiue_vert_index = -1
        for i, item in enumerate(sorted_verts):
            vert = item[0]
            original_index = item[1]
            # NOTE: lazy boolean eval
            if (current_unique_vert is None) or (max_abs_diff(vert, current_unique_vert) > 0.00001):
                current_unique_vert = vert
                current_unqiue_vert_index = i
                unique_verts.append(current_unique_vert)

            # update face vert indices
            # bad for cpu cache :(
            faces[original_index - 1] = current_unqiue_vert_index

    else:
        # Binary STL
        f.read(80 - 5)  # consume rest of 80 bytes header
        num_tri = struct.unpack("<I", f.read(4))[0]
        for i in range(num_tri):
            pass
