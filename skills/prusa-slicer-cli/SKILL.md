# PrusaSlicer CLI Automation

## Description

This skill automates the translation of 3D meshes (STL/OBJ) into machine-readable toolpaths (G-Code for FDM, or SL1/CTB for SLA/Resin) using PrusaSlicer's headless CLI.

## Slicing for FDM (e.g., Anycubic X, Prusa)

To slice an STL file into standard G-Code for FDM printers:

```bash
prusa-slicer --export-gcode --load fdm_printer_config.ini --output output.gcode input.stl
```

## Slicing for SLA/Resin (e.g., Creality Resin)

Resin printers use an SLA-specific slicing mode.

```bash
prusa-slicer --sla --export-sla --load sla_printer_config.ini --output output.sl1 input.stl
```

## Overriding Parameters on the Fly

You can override specific parameters like layer height, infill, or exposure time directly via the CLI:

```bash
prusa-slicer --export-gcode --layer-height 0.15 --fill-density 20% --output part.gcode part.stl
```

## Important Notes

1.  **Config Files:** You MUST specify a configuration file (`--load config.ini`) tailored to the specific printer model (e.g., Anycubic FDM vs Creality Resin) unless you want to pass every single machine limit via CLI arguments.
2.  **SLA vs FDM:** Never send FDM G-Code to a Resin printer or vice-versa. Always use `--sla` for resin slicing.

## Verifying Output

You can verify the output file was successfully generated and check its size:

```bash
ls -lh output.gcode
```
