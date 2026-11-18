import unittest

from PIL import Image, ImageDraw

from pdf_layout_engine import apply_background_removal


class BackgroundRemovalTests(unittest.TestCase):
    def _run_case(self, paper, ink, line_width=2, faint=False):
        image = Image.new("RGB", (120, 72), paper)
        draw = ImageDraw.Draw(image)
        draw.line((12, 34, 107, 34), fill=ink, width=line_width)
        draw.ellipse((62, 20, 64, 22), fill=ink)
        if faint:
            draw.line((16, 48, 92, 48), fill=(145, 145, 145), width=1)
        before = image.tobytes()
        result = apply_background_removal(image)
        self.addCleanup(result.close)
        self.addCleanup(image.close)
        self.assertEqual(image.tobytes(), before)
        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.size, (120, 72))
        self.assertEqual(result.getpixel((2, 2))[3], 0)
        self.assertGreater(result.getpixel((35, 34))[3], 180)
        self.assertEqual(result.getpixel((35, 34))[:3], tuple(ink))
        return result

    def test_white_paper_black_handwriting(self):
        self._run_case((255, 255, 255), (20, 20, 20))

    def test_grey_paper_grey_ink(self):
        self._run_case((205, 205, 205), (80, 80, 80))

    def test_cream_paper_blue_ink(self):
        self._run_case((239, 228, 204), (35, 75, 145))

    def test_uneven_lighting_preserves_faint_stroke(self):
        image = Image.new("RGB", (120, 72))
        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                value = 224 + round(25 * x / (image.width - 1))
                pixels[x, y] = (value, value, value)
        draw = ImageDraw.Draw(image)
        draw.line((12, 34, 107, 34), fill=(25, 25, 25), width=2)
        draw.line((16, 48, 92, 48), fill=(165, 165, 165), width=1)
        result = apply_background_removal(image)
        self.addCleanup(image.close)
        self.addCleanup(result.close)
        self.assertEqual(result.getpixel((5, 34))[3], 0)
        self.assertGreater(result.getpixel((40, 34))[3], 180)
        self.assertGreater(result.getpixel((40, 48))[3], 0)

    def test_beige_paper_and_signature_dots(self):
        self._run_case((224, 211, 184), (45, 43, 39), line_width=1)

    def test_low_contrast_stain_is_modeled_as_paper(self):
        image = Image.new("RGB", (120, 72), (224, 211, 184))
        draw = ImageDraw.Draw(image)
        draw.rectangle((42, 10, 72, 26), fill=(231, 218, 190))
        draw.line((12, 40, 107, 40), fill=(35, 35, 35), width=2)
        result = apply_background_removal(image)
        self.addCleanup(image.close)
        self.addCleanup(result.close)
        self.assertLessEqual(result.getpixel((55, 18))[3], 8)
        self.assertGreater(result.getpixel((55, 40))[3], 180)

    def test_selected_paper_color_and_original_alpha_are_respected(self):
        image = Image.new("RGBA", (12, 8), (236, 224, 205, 180))
        image.putpixel((6, 4), (40, 70, 120, 128))
        result = apply_background_removal(image, {
            "background_color": "#ece0cd", "adaptive": False,
        })
        self.addCleanup(image.close)
        self.addCleanup(result.close)
        self.assertEqual(result.getpixel((1, 1))[3], 0)
        self.assertGreater(result.getpixel((6, 4))[3], 0)
        self.assertLessEqual(result.getpixel((6, 4))[3], 128)
        self.assertEqual(result.getpixel((6, 4))[:3], (40, 70, 120))


if __name__ == "__main__":
    unittest.main()
