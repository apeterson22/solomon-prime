# OpenSCAD Automation

## Description

This skill provides automation for creating, modifying, and compiling parametric 3D models using OpenSCAD via the command line interface (CLI).

## Usage

When working with OpenSCAD, use the following patterns:

### 1. Generating a Mesh (STL) from SCAD

To compile a `.scad` script into a 3D printable `.stl` file without human intervention:

```bash
openscad -o output.stl input.scad
```

### 2. Passing Parameters via CLI

You can pass custom variables to your parametric SCAD scripts on the fly:

```bash
openscad -D "width=50" -D "length=100" -o custom_part.stl parametric_part.scad
```

### 3. Visual Verification (PNG Render)

Before slicing, it's highly recommended to generate visual previews to verify structural integrity (manifold geometry, overhangs). Use a specific camera angle or let OpenSCAD auto-center:

```bash
openscad -o render_preview.png --colorscheme="Tomorrow" --imgsize=1024,1024 input.scad
```

_Note: Use the `image` tool to inspect `render_preview.png` after generation._

### 4. Code Generation Best Practices

- **Modularity:** Keep OpenSCAD code modular by using `module()` definitions.
- **Resolution:** Always define `$fn` for smooth curves (e.g., `$fn=100;` for high-res final prints, `$fn=32;` for fast draft renders).
- **Manifold Geometries:** Ensure overlapping parts have slight intersections to prevent non-manifold edges.

## Error Handling

If OpenSCAD throws "CGAL error", the geometry is non-manifold. Re-check the intersections.
