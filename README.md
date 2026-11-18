# PDF Layout Engine

A Python/Tkinter desktop tool for designing reusable multipage PDF layouts with draggable text and image placeholders, template save/load, PDF preview and export, JPG/PNG raster downloads, PNG transparency/cropping, and adaptive paper-background removal (BGRem).

## Requirements

- Python 3.10+
- Pillow
- ReportLab
- PyMuPDF
- Tkinter (included with most standard Windows Python installations)

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run on Windows:

```bash
python pdf_layout_engine.py
```

## Features

- Multi-page background images and reusable layout templates
- Dynamic numbered text and image inputs
- Text styling, positioning, rotation, resizing, layers, undo/redo, zoom, grid and snapping
- PNG alpha preservation, image opacity, crop and fit modes
- PDF preview and PDF/JPG/PNG exports
- Adaptive BGRem for uneven white, grey, cream, beige and yellowed paper backgrounds

## Tests

Run the automated tests with:

```bash
python -m unittest discover -s tests -v
```

## Notes

This is a local desktop application. Cloud sync and a phone-based web interface are not included.
