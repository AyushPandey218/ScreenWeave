import unittest
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from app.typography import text_style, FONT_PATHS, BOLD_PATHS

class TypographyTests(unittest.TestCase):
    def test_colored_text_size(self):
        font_path = next((p for p in FONT_PATHS if p.is_file()), None)
        if font_path is None:
            self.skipTest('No reference font')
        image = Image.new('RGB', (360, 100), 'white')
        draw = ImageDraw.Draw(image)
        draw.text((20, 20), 'Welcome back', fill='#b42348', font=ImageFont.truetype(str(font_path), 24))
        result = text_style(np.asarray(image), {'x': 18, 'y': 22, 'width': 180, 'height': 30, 'text': 'Welcome back'})
        self.assertEqual(result['color'], '#b42348')
        self.assertAlmostEqual(result['font_size'], 24, delta=2)

    def test_blank_region(self):
        self.assertEqual(text_style(np.full((30, 100, 3), 255, dtype=np.uint8), {'x': 0, 'y': 0, 'width': 100, 'height': 30, 'text': ''}), {})


    def test_regular_and_bold_weight(self):
        for weight, paths in ((400, FONT_PATHS), (700, BOLD_PATHS)):
            font_path = next((p for p in paths if p.is_file()), None)
            if font_path is None:
                self.skipTest('No reference font')
            image = Image.new('RGB', (500, 100), 'white')
            draw = ImageDraw.Draw(image)
            draw.text((20, 20), 'ScreenWeave studio', fill='#172e30', font=ImageFont.truetype(str(font_path), 28))
            result = text_style(np.asarray(image), {'x': 15, 'y': 15, 'width': 350, 'height': 60, 'text': 'ScreenWeave studio'})
            self.assertEqual(result['font_weight'], weight)
            self.assertAlmostEqual(result['font_size'], 28, delta=2)

    def test_font_families(self):
        from app.typography import FONT_FAMILIES
        for family, (regular, _) in FONT_FAMILIES.items():
            path = next((p for p in regular if p.is_file()), None)
            if path is None:
                continue
            image=Image.new('RGB',(500,100),'white')
            ImageDraw.Draw(image).text((20,20),'ScreenWeave studio',fill='#172e30',font=ImageFont.truetype(str(path),28))
            result=text_style(np.asarray(image),{'x':15,'y':15,'width':400,'height':60,'text':'ScreenWeave studio'})
            self.assertEqual(result['font_family'],family)
