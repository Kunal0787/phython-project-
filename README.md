# PDF Layout Engine

A local Python/Tkinter desktop application for designing reusable, multi-page PDF layouts. It lets you place editable text and image placeholders over background pages, save layouts as templates, and generate PDFs or page images.

## Features

- Multi-page background images and reusable layout templates
- Draggable, resizable, rotatable text and image placeholders
- Dynamically numbered text and image inputs
- Text styling: font, size, color, alignment, opacity, stroke, shadow, character/word spacing, line spacing and paragraph spacing
- Image crop, rotation, flip, fit modes and opacity
- Adaptive BGRem for white, grey, cream, beige and yellowed paper, including uneven lighting
- PDF preview and PDF/JPG/PNG export
- PNG transparency preservation
- Save and reload layout templates

## Restore the application source

To keep the large Python source file manageable in this repository, it is stored as six compressed Base64 text parts under `source/`. Reconstruct the runnable Python file once after cloning or downloading the repository:

```bash
python restore_source.py
```

The restore script checks the reconstructed source file's size and SHA-256 checksum before writing `pdf_layout_engine.py`.

## Install and run (Windows)

Python 3.10 or later is recommended. Tkinter is included with the standard Windows Python installer.

```bash
python -m pip install -r requirements.txt
python restore_source.py
python pdf_layout_engine.py
```

## Run the tests

After restoring the source and installing dependencies:

```bash
python -m unittest discover -s tests -v
```

The test suite covers adaptive paper-background removal, preservation of PNG alpha and crop data, PDF rendering of transparent images, and multi-page JPG/PNG export. The 19 tests passed in the local verification performed for this upload.

## Optional Special Elite font

The original ZIP includes the `SpecialElite-Regular.ttf` font. The font binary is not included in this GitHub repository. The application continues to work with its other built-in fonts; the Special Elite option is hidden when its font file is absent. To restore that font, copy `SpecialElite-Regular.ttf` from the original ZIP into a `fonts/` folder beside `pdf_layout_engine.py`.

## Notes

- This is a local desktop application. Cloud sync and a phone-based web interface are not included.
- Generated PDFs and exported page images are local output files and are excluded from Git by `.gitignore`.
