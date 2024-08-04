Schematic Generation
======
## Program Overview
This program utilizes KiCAD's S-expression specification to create schematics in KiCAD schematic files.
## Program Description
1. Schematic Generation (the program has two entry points):
  - loop_generator.py implements the main program for schematic generation.
  
2. The following programs are called by the main programs above:
  - kicad_selector.py for component symbol selection
  - kicad_writer.py for writing into schematic files
  - kicad_sym.py for parsing KiCAD formats, such as how symbols are parsed
  - sexpr.py is an official file provided for parsing KiCAD files, which is called by kicad_sym.py
