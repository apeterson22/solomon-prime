#!/bin/bash
# Autonomous Code-to-GCode Pipeline
# Converts OpenSCAD parameters -> STL -> FDM GCode & SLA sliced files

set -e

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <scad_file> <fdm_config.ini> <sla_config.ini> [output_prefix]"
    exit 1
fi

SCAD_FILE=$1
FDM_CONFIG=$2
SLA_CONFIG=$3
PREFIX=${4:-"autonomous_build"}

STL_FILE="${PREFIX}.stl"
FDM_OUT="${PREFIX}_fdm.gcode"
SLA_OUT="${PREFIX}_sla.sl1"
PNG_PREVIEW="${PREFIX}_preview.png"

echo "=== Code-to-GCode Pipeline Started ==="
echo "Target SCAD: $SCAD_FILE"

# Step 1: Render Verification Preview
echo "[1/4] Generating visual preview..."
openscad -o "$PNG_PREVIEW" --colorscheme="Tomorrow" --imgsize=1024,1024 "$SCAD_FILE" || { echo "Failed to generate preview"; exit 1; }
echo "Preview saved to $PNG_PREVIEW"

# Step 2: Compile STL
echo "[2/4] Compiling STL mesh..."
openscad -o "$STL_FILE" "$SCAD_FILE" || { echo "Failed to compile STL"; exit 1; }
echo "STL saved to $STL_FILE"

# Step 3: Slice for FDM (Anycubic X)
echo "[3/4] Slicing for FDM..."
if command -v prusa-slicer &> /dev/null; then
    prusa-slicer --export-gcode --load "$FDM_CONFIG" --output "$FDM_OUT" "$STL_FILE" || { echo "Failed FDM Slicing"; exit 1; }
    echo "FDM G-Code saved to $FDM_OUT"
else
    echo "WARNING: prusa-slicer not found in PATH. Skipping FDM slice."
fi

# Step 4: Slice for SLA (Creality Resin)
echo "[4/4] Slicing for SLA..."
if command -v prusa-slicer &> /dev/null; then
    prusa-slicer --sla --export-sla --load "$SLA_CONFIG" --output "$SLA_OUT" "$STL_FILE" || { echo "Failed SLA Slicing"; exit 1; }
    echo "SLA sliced file saved to $SLA_OUT"
else
    echo "WARNING: prusa-slicer not found in PATH. Skipping SLA slice."
fi

echo "=== Pipeline Complete ==="
