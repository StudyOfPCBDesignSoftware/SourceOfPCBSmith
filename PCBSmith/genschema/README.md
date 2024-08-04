Schematic Generation
======
## Program Overview
In Electronic Design Automation (EDA), Printed
Circuit Board (PCB) design plays a crucial role. Verifying
the reliability of the PCB design tool chain is essential, as
bugs in the tool chain can cause significant issues and losses
during design and production. To improve reliability, a key
process is to generate numerous PCB schematics and execute
them in the tool chain, to test the correctness of each tool
chain functionality. However, it is a challenge to automatically
generate valid schematics that reflect real-world circuit diagram
distribution to simulate the actual use of the PCB design tool
chain. To this end, we propose PCBSmith, an effective schematic
generator for PCB design tool chain. PCBSmith mimics the steps
of a PCB designer for schematic design. PCBSmith first selects
the appropriate electronic components from a comprehensive
library and connects them according to the constraints of
different components. PCBSmith then sets electrical parameters
and simulation models for each component, eventually generating simulatable schematic.
## Program Description
1. Schematic Generation (the program has two entry points):
  - loop_generator.py implements the main program for schematic generation.
  
2. The following programs are called by the main programs above:
  - kicad_selector.py for component symbol selection
  - kicad_writer.py for writing into schematic files
  - kicad_sym.py for parsing KiCAD formats, such as how symbols are parsed
  - sexpr.py is an official file provided for parsing KiCAD files, which is called by kicad_sym.py
