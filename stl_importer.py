bl_info = {
    "name": "Fast STL importer",
    "author": "Iyad Ahmed (Twitter: @cgonfire)",
    "version": (0, 0, 1),
    "blender": (2, 93, 4),
    "category": "Import-Export",
}


import struct
from enum import Enum, auto
from pathlib import PurePath
from typing import BinaryIO

import bmesh
import bpy
import bpy_extras
from timeit import default_timer
from contextlib import contextmanager


@contextmanager
def execution_timer(msg: str):
    t0 = default_timer()
    yield
    t1 = default_timer()
    print(f"{msg} finished in {t1 - t0} sec")


class FSTL_OT_import_stl(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "fstl.import_stl"
    bl_label = "Fast STL import"
    bl_options = {"REGISTER", "UNDO"}

    filter_glob: bpy.props.StringProperty(default="*.stl", options={"HIDDEN"})

    def execute(self, context):
        with execution_timer(f"Importing STL {self.filepath}"):
            obj = read_stl(self.filepath)
            bpy.context.collection.objects.link(obj)
        return {"FINISHED"}


def object_from_bmesh(name: str, bm: bmesh.types.BMesh):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    return obj


class STLType(Enum):
    ASCII = auto()
    BINARY = auto()


def _read_stl_header(file: BinaryIO):
    first_5_bytes = file.read(5)
    if first_5_bytes == b"solid":
        return STLType.ASCII, first_5_bytes + file.readline()

    return STLType.BINARY, first_5_bytes + file.read(80 - 5)


# TODO: make code more robust against "bad" STLs
# TODO: investigate benefits of using bmesh.ops.remove_doubles
# TODO: investigate benefits of using file.seek to skip "unneeded" data


def _read_stl_ascii(file: BinaryIO):
    # you should read header before this
    bm_verts = dict()
    bm_mesh = bmesh.new(use_operators=False)
    current_facet_verts = []
    for line in file.readlines():
        stripped_line = line.strip()
        if stripped_line.startswith(b"vertex"):
            bm_vert = bm_verts.get(stripped_line, None)
            if bm_vert is None:
                vertex_str = stripped_line.rsplit(b" ", 3)[-3:]
                vertex_vec = (float(s) for s in vertex_str)
                bm_vert = bm_mesh.verts.new(vertex_vec)
                bm_verts[stripped_line] = bm_vert

            current_facet_verts.append(bm_vert)

        elif stripped_line.startswith(b"endfacet"):
            bm_mesh.faces.new(current_facet_verts)
            current_facet_verts.clear()

    obj = object_from_bmesh(PurePath(file.name).stem, bm_mesh)
    bm_mesh.free()

    return obj


def _read_stl_bin(file: BinaryIO):
    # assuming header has been read
    num_tri = struct.unpack("<I", file.read(struct.calcsize("<I")))[0]
    bm_verts = dict()
    bm_mesh = bmesh.new(use_operators=False)
    for i in range(num_tri):
        normal_bytes = file.read(struct.calcsize("<3f"))
        current_face_verts = []
        for _ in range(3):
            vertex_vec_bytes = file.read(struct.calcsize("<3f"))
            bm_vert = bm_verts.get(vertex_vec_bytes, None)
            if bm_vert is None:
                bm_vert = bm_mesh.verts.new(struct.unpack("<3f", vertex_vec_bytes))
                bm_verts[vertex_vec_bytes] = bm_vert

            current_face_verts.append(bm_vert)

        bm_mesh.faces.new(current_face_verts)

        file.read(struct.calcsize("<H"))

    obj = object_from_bmesh(PurePath(file.name).stem, bm_mesh)
    bm_mesh.free()

    return obj


def read_stl(filepath):
    with open(filepath, "rb") as file:
        stl_type, header = _read_stl_header(file)
        if stl_type == STLType.ASCII:
            return _read_stl_ascii(file)

        return _read_stl_bin(file)


def draw_fast_import_stl(self, context):
    self.layout.operator(FSTL_OT_import_stl.bl_idname)


def register():
    bpy.utils.register_class(FSTL_OT_import_stl)
    bpy.types.TOPBAR_MT_file_import.append(draw_fast_import_stl)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(draw_fast_import_stl)
    bpy.utils.unregister_class(FSTL_OT_import_stl)
