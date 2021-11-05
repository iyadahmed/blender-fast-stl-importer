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


class FSTL_OT_import_stl(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "fstl.import_stl"
    bl_label = "Fast STL import"
    bl_options = {"REGISTER", "UNDO"}

    filter_glob: bpy.props.StringProperty(default="*.stl", options={"HIDDEN"})

    def execute(self, context):
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


def _read_stl_ascii(file: BinaryIO):
    # you should read header before this
    bm_verts = dict()
    bm_mesh = bmesh.new(use_operators=False)
    current_facet_verts = []
    # normals = []
    for line in file.readlines():
        stripped_line = line.strip()
        # if stripped_line.startswith(b"facet"):
        # normal_str = stripped_line.rsplit(b" ", 3)[-3:]
        # normal = [float(s) for s in normal_str]
        # normals.append(normal)
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
    # you should read header before this
    num_tri = struct.unpack("<I", file.read(4))[0]
    for i in range(num_tri):
        pass


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
