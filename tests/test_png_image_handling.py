import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pdf_layout_engine import (
    PDFLayoutApp,
    apply_image_edit,
    apply_image_opacity,
    export_pdf_pages_as_raster,
    native_export_page_sizes,
    safe_open_rgba_image,
)

try:
    import pymupdf
except ModuleNotFoundError:
    import fitz as pymupdf


class PngImageHandlingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def _write_background(self):
        path = self.root / "background.png"
        Image.new("RGB", (40, 20), "white").save(path, format="PNG")
        return path

    def _write_color_strip(self, name, colors):
        path = self.root / name
        image = Image.new("RGBA", (len(colors), 2))
        for x, color in enumerate(colors):
            for y in range(2):
                image.putpixel((x, y), color)
        image.save(path, format="PNG", compress_level=9)
        image.close()
        return path

    def _render_image_placeholder(self, image_path, edit=None, element_settings=None):
        background_path = self._write_background()
        output_path = self.root / f"{image_path.stem}_output.pdf"
        app = PDFLayoutApp.__new__(PDFLayoutApp)
        template = {
            "backgrounds": [{"path": str(background_path)}],
            "elements": [{**{
                "id": 1, "type": "image", "key": "IMAGE1", "page": 0,
                "x": 0, "y": 0, "w": 100, "h": 100, "fit": "contain",
                "rotation": 0, "remove_background": False,
                "image_edit": edit or {"crop": [0, 0, 1, 1]},
            }, **(element_settings or {})}],
        }
        app._render_pdf(output_path, template, {}, {"IMAGE1": str(image_path)})
        return output_path

    def _render_page(self, pdf_path):
        document = pymupdf.open(str(pdf_path))
        self.addCleanup(document.close)
        page = document[0]
        pixmap = page.get_pixmap(dpi=96, colorspace=pymupdf.csRGB, alpha=False)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        self.addCleanup(image.close)
        return page, image

    def test_rgba_png_pixels_and_alpha_are_decoded_without_changes(self):
        transparent_png = self._write_color_strip(
            "rgba.png", [(12, 34, 56, 0), (90, 120, 150, 127), (210, 180, 30, 255)]
        )
        before = hashlib.sha256(transparent_png.read_bytes()).digest()

        opened = safe_open_rgba_image(transparent_png)
        self.addCleanup(opened.close)

        with Image.open(transparent_png) as original:
            expected = original.convert("RGBA")
        self.addCleanup(expected.close)
        self.assertEqual(opened.size, (3, 2))
        self.assertEqual(opened.tobytes(), expected.tobytes())
        self.assertEqual(hashlib.sha256(transparent_png.read_bytes()).digest(), before)

    def test_palette_png_transparency_is_preserved(self):
        path = self.root / "palette_transparency.png"
        image = Image.new("P", (2, 1))
        image.putpalette([255, 0, 0, 0, 200, 40] + [0, 0, 0] * 254)
        image.putdata([0, 1])
        image.info["transparency"] = bytes([0, 255])
        image.save(path, format="PNG")
        image.close()

        decoded = safe_open_rgba_image(path)
        self.addCleanup(decoded.close)
        self.assertEqual(decoded.getpixel((0, 0)), (255, 0, 0, 0))
        self.assertEqual(decoded.getpixel((1, 0)), (0, 200, 40, 255))

    def test_crop_is_non_destructive_and_keeps_alpha(self):
        path = self._write_color_strip(
            "crop_source.png", [(255, 0, 0, 0), (0, 255, 0, 64), (0, 0, 255, 128), (255, 255, 0, 255)]
        )
        before = hashlib.sha256(path.read_bytes()).digest()
        source = safe_open_rgba_image(path)
        self.addCleanup(source.close)

        crop = apply_image_edit(source, {"crop": [0.5, 0, 1, 1]})
        self.addCleanup(crop.close)
        self.assertEqual(crop.size, (2, 2))
        self.assertEqual(crop.getpixel((0, 0)), (0, 0, 255, 128))
        self.assertEqual(crop.getpixel((1, 0)), (255, 255, 0, 255))
        self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), before)

    def test_opacity_multiplier_preserves_source_alpha_and_color(self):
        source = Image.new("RGBA", (2, 1))
        self.addCleanup(source.close)
        source.putpixel((0, 0), (20, 40, 60, 200))
        source.putpixel((1, 0), (90, 120, 150, 0))

        faded = apply_image_opacity(source, 50)
        self.addCleanup(faded.close)

        self.assertEqual(faded.getpixel((0, 0)), (20, 40, 60, 100))
        self.assertEqual(faded.getpixel((1, 0)), (90, 120, 150, 0))

    def test_image_opacity_is_applied_in_pdf_export(self):
        path = self._write_color_strip("semi_transparent.png", [(255, 0, 0, 255)])
        pdf_path = self._render_image_placeholder(path, element_settings={"opacity": 50})
        _page, rendered = self._render_page(pdf_path)
        pixel = rendered.getpixel((rendered.width // 2, rendered.height // 2))
        self.assertLessEqual(abs(pixel[0] - 255), 2)
        self.assertLessEqual(abs(pixel[1] - 127), 2)
        self.assertLessEqual(abs(pixel[2] - 127), 2)

    def test_original_fit_preserves_source_pixel_size_in_pdf(self):
        path = self.root / "native_size.png"
        Image.new("RGB", (4, 2), "blue").save(path, format="PNG")
        pdf_path = self._render_image_placeholder(
            path, element_settings={"fit": "original"}
        )
        _page, rendered = self._render_page(pdf_path)
        self.assertEqual(rendered.getpixel((20, 10)), (0, 0, 255))
        self.assertEqual(rendered.getpixel((16, 10)), (255, 255, 255))

    def test_saved_bgrem_settings_are_used_by_pdf_renderer(self):
        path = self.root / "cream_ink.png"
        image = Image.new("RGB", (4, 2), (236, 224, 205))
        image.putpixel((1, 0), (20, 30, 50))
        image.save(path, format="PNG")
        image.close()
        pdf_path = self._render_image_placeholder(path, element_settings={
            "remove_background": True,
            "background_removal": {
                "background_color": "#ece0cd", "adaptive": False,
            },
        })
        _page, rendered = self._render_page(pdf_path)
        self.assertEqual(rendered.getpixel((18, 10)), (255, 255, 255))
        self.assertLess(rendered.getpixel((19, 9))[0], 80)

    def test_pdf_keeps_transparency_and_renders_png_colors(self):
        path = self._write_color_strip(
            "transparent_overlay.png",
            [(20, 40, 60, 0), (255, 0, 0, 128), (0, 0, 255, 255), (0, 255, 0, 255)],
        )
        pdf_path = self._render_image_placeholder(path)
        page, rendered = self._render_page(pdf_path)
        self.assertTrue(any(image_info[1] for image_info in page.get_images(full=True)))
        expected = ((255, 255, 255), (255, 127, 127), (0, 0, 255), (0, 255, 0))
        for source_x, color in enumerate(expected):
            pixel = rendered.getpixel((source_x * 10 + 5, rendered.height // 2))
            for actual, wanted in zip(pixel, color):
                self.assertLessEqual(abs(actual - wanted), 2)

    def test_cropped_png_appears_in_final_pdf_without_modifying_source(self):
        path = self._write_color_strip(
            "cropped_overlay.png",
            [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)],
        )
        before = hashlib.sha256(path.read_bytes()).digest()
        pdf_path = self._render_image_placeholder(path, {"crop": [0.5, 0, 1, 1]})
        _page, rendered = self._render_page(pdf_path)
        self.assertEqual(rendered.getpixel((5, rendered.height // 2)), (255, 255, 255))
        self.assertEqual(rendered.getpixel((15, rendered.height // 2)), (0, 0, 255))
        self.assertEqual(rendered.getpixel((25, rendered.height // 2)), (255, 255, 0))
        self.assertEqual(rendered.getpixel((35, rendered.height // 2)), (255, 255, 255))
        self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), before)

    def test_raster_export_uses_highest_source_image_density_on_page(self):
        path = self.root / "high_resolution_overlay.png"
        Image.new("RGBA", (400, 200), (30, 90, 180, 180)).save(path, format="PNG")
        Image.new("RGB", (40, 20), "white").save(self.root / "background.png", format="PNG")
        template = {
            "backgrounds": [{"path": str(self.root / "background.png")}],
            "elements": [{
                "type": "image", "key": "IMAGE1", "page": 0,
                "x": 0, "y": 0, "w": 100, "h": 100, "fit": "contain",
            }],
        }
        image_values = {"IMAGE1": str(path)}
        self.assertEqual(native_export_page_sizes(template, image_values), [(400, 200)])
        pdf_path = self._render_image_placeholder(path)
        raster_paths = export_pdf_pages_as_raster(
            pdf_path, self.root / "full_resolution.png", "PNG",
            page_pixel_sizes=native_export_page_sizes(template, image_values),
        )
        with Image.open(raster_paths[0]) as raster:
            self.assertEqual(raster.format, "PNG")
            self.assertEqual(raster.size, (400, 200))


if __name__ == "__main__":
    unittest.main()
