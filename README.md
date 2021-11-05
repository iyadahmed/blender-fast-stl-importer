# blender-fast-stl-importer

Fast STL (ASCII & Binary) importer for Blender

Technical notes:
- floats are not parsed if the vertex was read before (the bytes are used as hash)
- mesh is created as the file is read
- simple code base no over engineering
