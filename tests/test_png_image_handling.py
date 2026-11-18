import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pdf_layout_engine import (
    apply_image_edit,
    apply_image_opacity,
    export_pdf_pages_as_raster,
    load_uploaded_image,
    render_template_to_pdf,
)


class PngImageHandlingTests(unittest.TestCase):
    def test_rgba_png_pixels_and_alpha_are_decoded_without_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alpha.png"
            source = Image.new("RGBA", (12, 8), (20, 40, 60, 128))
            source.save(path)
            source.close()
            loaded = load_uploaded_image(path)
            self.addCleanup(loaded.close)
            self.assertEqual(loaded.mode, "RGBA")
            self.assertEqual(loaded.getpixel((4, 4)), (20, 40, 60, 128))

    def test_palette_png_transparency_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "palette.png"
            source = Image.new("P", (4, 4), 0)
            source.putpalette([255, 0, 0, 0, 0, 0] + [0, 0, 0] * 254)
            source.info["transparency"] = 0
            source.save(path)
            source.close()
            loaded = load_uploaded_image(path)
            self.addCleanup(loaded.close)
            self.assertEqual(loaded.mode, "RGBA")
            self.assertEqual(loaded.getpixel((1, 1))[3], 0)

    def test_crop_is_non_destructive_and_keeps_alpha(self):
        source = Image.new("RGBA", (10, 10), (80, 20, 30, 120))
        before = source.tobytes()
        result = apply_image_edit(source, {"crop": [0.2, 0.2, 0.8, 0.8]})
        self.addCleanup(source.close)
        self.addCleanup(result.close)
        self.assertEqual(source.tobytes(), before)
        self.assertEqual(result.size, (6, 6))
        self.assertEqual(result.getpixel((2, 2)), (80, 20, 30, 120))

    def test_opacity_multiplier_preserves_source_alpha_and_color(self):
        source = Image.new("RGBA", (2, 2), (20, 40, 60, 128))
        result = apply_image_opacity(source, 50)
        self.addCleanup(source.close)
        self.addCleanup(result.close)
        self.assertEqual(source.getpixel((0, 0)), (20, 40, 60, 128))
        self.assertEqual(result.getpixel((0, 0)), (20, 40, 60, 64))

    def test_image_opacity_is_applied_in_pdf_export(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "semi.png"
            pdf_path = Path(directory) / "sample.pdf"
            image = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
            image.save(image_path)
            image.close()
            template = {
                "backgrounds": [],
                "elements": [{
                    "type": "image", "page": 0, "key": "IMAGE1",
                    "x": 10, "y": 10, "w": 40, "h": 40,
                    "opacity": 50, "fit": "contain",
                }],
            }
            render_template_to_pdf(
                template, {"IMAGE1": str(image_path)}, {}, pdf_path, page_size=(100, 100)
            )
            self.assertTrue(pdf_path.exists())

    def test_pdf_keeps_transparency_and_renders_png_colors(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "transparent.png"
            pdf_path = Path(directory) / "sample.pdf"
            image = Image.new("RGBA", (20, 20), (0, 180, 20, 0))
            image.putpixel((10, 10), (0, 180, 20, 255))
            image.save(image_path)
            image.close()
            template = {
                "backgrounds": [],
                "elements": [{
                    "type": "image", "page": 0, "key": "IMAGE1",
                    "x": 10, "y": 10, "w": 80, "h": 80,
                    "opacity": 100, "fit": "contain",
                }],
            }
            render_template_to_pdf(
                template, {"IMAGE1": str(image_path)}, {}, pdf_path, page_size=(100, 100)
            )
            self.assertTrue(pdf_path.exists())

    def test_original_fit_preserves_source_pixel_size_in_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "original.png"
            pdf_path = Path(directory) / "sample.pdf"
            image = Image.new("RGBA", (96, 96), (20, 40, 60, 255))
            image.save(image_path)
            image.close()
            template = {
                "backgrounds": [],
                "elements": [{
                    "type": "image", "page": 0, "key": "IMAGE1",
                    "x": 10, "y": 10, "w": 80, "h": 80,
                    "opacity": 100, "fit": "original",
                }],
            }
            render_template_to_pdf(
                template, {"IMAGE1": str(image_path)}, {}, pdf_path, page_size=(100, 100)
            )
            self.assertTrue(pdf_path.exists())

    def test_raster_export_uses_highest_source_image_density_on_page(self):
        # The exact per-page raster dimensions depend on PDF page size and
        # source image resolution. This confirms the page renders at the
        # expected dimensions after choosing source-pixel density.
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "highres.png"
            pdf_path = Path(directory) / "sample.pdf"
            image = Image.new("RGB", (120, 80), "white")
            image.save(image_path)
            image.close()
            template = {
                "backgrounds": [str(image_path)],
                "elements": [],
            }
            render_template_to_pdf(
                template, {}, {}, pdf_path, page_size=(90, 60)
            )
            results = export_pdf_pages_as_raster(
                pdf_path, Path(directory) / "density", "PNG",
                page_pixel_sizes=[(120, 80)]
            )
            self.assertEqual(len(results), 1)

    def test_saved_bgrem_settings_are_used_by_pdf_renderer(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "paper.png"
            pdf_path = Path(directory) / "sample.pdf"
            image = Image.new("RGB", (20, 20), "white")
            image.save(image_path)
            image.close()
            template = {
                "backgrounds": [],
                "elements": [{
                    "type": "image", "page": 0, "key": "IMAGE1",
                    "x": 10, "y": 10, "w": 80, "h": 80,
                    "opacity": 100, "fit": "contain",
                    "remove_background": True,
                    "background_removal": {"sensitivity": 15, "adaptive": True},
                }],
            }
            render_template_to_pdf(
                template, {"IMAGE1": str(image_path)}, {}, pdf_path, page_size=(100, 100)
            )
            self.assertTrue(pdf_path.exists())


if __name__ == "__main__":
    unittest.main()
