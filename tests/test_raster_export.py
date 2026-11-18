import tempfile
import unittest
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas

from pdf_layout_engine import export_pdf_pages_as_raster


class RasterExportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.pdf_path = self.root / "two_pages.pdf"

        pdf = canvas.Canvas(str(self.pdf_path), pagesize=(72, 72))
        pdf.setFillColorRGB(1, 0, 0)
        pdf.rect(0, 0, 72, 72, fill=1)
        pdf.showPage()
        pdf.setFillColorRGB(0, 0, 1)
        pdf.rect(0, 0, 72, 72, fill=1)
        pdf.showPage()
        pdf.save()

    def test_multipage_jpeg_export_writes_real_jpegs(self):
        output = self.root / "download.jpg"

        pages = export_pdf_pages_as_raster(self.pdf_path, output, "JPEG", dpi=72)

        self.assertEqual(
            [path.name for path in pages],
            ["download_page_01.jpg", "download_page_02.jpg"],
        )
        for path in pages:
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes()[:3], b"\xff\xd8\xff")
            with Image.open(path) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(image.size, (72, 72))
                self.assertAlmostEqual(image.info["dpi"][0], 72, delta=1)
                self.assertAlmostEqual(image.info["dpi"][1], 72, delta=1)

        self.assertEqual(self.pdf_path.read_bytes()[:4], b"%PDF")

    def test_multipage_png_export_remains_png(self):
        pages = export_pdf_pages_as_raster(
            self.pdf_path, self.root / "download.png", "PNG", dpi=72
        )

        self.assertEqual(len(pages), 2)
        self.assertEqual([path.suffix for path in pages], [".png", ".png"])
        for path in pages:
            with Image.open(path) as image:
                self.assertEqual(image.format, "PNG")
                self.assertAlmostEqual(image.info["dpi"][0], 72, delta=1)
                self.assertAlmostEqual(image.info["dpi"][1], 72, delta=1)


if __name__ == "__main__":
    unittest.main()
