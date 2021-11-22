# blender-fast-stl-importer

Fast STL (ASCII & Binary) importer for Blender  
based on https://en.wikipedia.org/wiki/STL_(file_format)

Technical notes:
- floats are not parsed if the vertex was read before (the bytes are used as dictionary key)
- mesh is created as the file is read
- simple code base no over engineering
