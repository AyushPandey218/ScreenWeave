"""Regression checks for rounded controls, nested shapes, and cropped curved graphics."""
import base64
import io
import unittest

import numpy as np
from PIL import Image, ImageDraw

from app.shapes import detect_shapes
from reconstruct import export


class ShapeTests(unittest.TestCase):
    def test_corner_radii(self):
        for radius in (0, 8, 20, 30):
            with self.subTest(radius=radius):
                image = Image.new('RGB', (420, 150), 'white')
                ImageDraw.Draw(image).rounded_rectangle((40, 40, 380, 100), radius=radius, fill='#2563eb')
                shapes = detect_shapes(np.asarray(image), [])
                self.assertEqual(len(shapes), 1)
                self.assertAlmostEqual(shapes[0]['radius'], radius, delta=5)

    def test_nested_outlined_pill(self):
        image = Image.new('RGB', (500, 400), '#eeeeee')
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((30, 30, 470, 370), radius=28, fill='white', outline='#334155', width=2)
        draw.rounded_rectangle((70, 100, 430, 160), radius=30, fill='white', outline='#334155', width=2)
        shapes = detect_shapes(np.asarray(image), [])
        self.assertEqual(len(shapes), 2)
        self.assertGreater(shapes[1]['radius'], 20)
        self.assertNotEqual(shapes[1]['border'], shapes[1]['background'])

    def test_curved_icon_is_preserved(self):
        image = Image.new('RGB', (180, 150), 'white')
        draw = ImageDraw.Draw(image)
        draw.arc((45, 40, 105, 100), 30, 310, fill='#2563eb', width=6)
        shapes = detect_shapes(np.asarray(image), [])
        self.assertEqual(len(shapes), 1)
        shape = shapes[0]
        self.assertIn('src', shape)
        decoded = Image.open(io.BytesIO(base64.b64decode(shape['src'].split(',')[1])))
        x, y, w, h = (shape[k] for k in ('x', 'y', 'width', 'height'))
        np.testing.assert_array_equal(np.asarray(decoded), np.asarray(image)[y:y+h, x:x+w])

    def test_ocr_text_is_not_an_icon(self):
        image = Image.new('RGB', (120, 100), 'white')
        ImageDraw.Draw(image).ellipse((30, 20, 60, 60), outline='black', width=2)
        text = {'x': 28, 'y': 18, 'width': 35, 'height': 45}
        self.assertEqual(detect_shapes(np.asarray(image), [text]), [])

    def test_export_uses_estimated_radius(self):
        layout = {'background': '#fff', 'viewport': {'width': 400, 'height': 200}, 'elements': [{'id': 'pill', 'type': 'input', 'x': 10, 'y': 10, 'width': 300, 'height': 60, 'radius': 30, 'background': '#fff', 'border': '#333'}]}
        _, css = export(layout)
        self.assertIn('border-radius:30px', css)


if __name__ == '__main__':
    unittest.main()
