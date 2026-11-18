import tempfile
import unittest
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas

from pdf_layout_engine import export_pdf_pages_as_raster


class RasterExportTests(unittest.TestCase):
    def _make_pdf(self, path):
        pdf = canvas.Canvas(str(path), pagesize=(120, 80))
        pdf.drawString(10, 40, "Raster export test")
        pdf.showPage()
        pdf.drawString(10, 40, "Second page")
        pdf.showPage()
        pdf.save()

    def test_multipage_jpeg_export_writes_real_jpegs(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "sample.pdf"
            output_path = Path(directory) / "export"
            self._make_pdf(pdf_path)
            results = export_pdf_pages_as_raster(
                pdf_path, output_path, "JPEG", dpi=72
            )
            self.assertEqual(len(results), 2)
            for path in results:
                with Image.open(path) as image:
                    self.assertEqual(image.format, "JPEG")

    def test_multipage_png_export_remains_png(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "sample.pdf"
            output_path = Path(directory) / "export"
            self._make_pdf(pdf_path)
            results = export_pdf_pages_as_raster(
                pdf_path, output_path, "PNG", dpi=72
            )
            self.assertEqual(len(results), 2)
            for path in results:
                with Image.open(path) as image:
                    self.assertEqual(image.format, "PNG")


if __name__ == "__main__":
    unittest.main()
