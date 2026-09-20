"""Infer text color and an approximate Arial-compatible font size from pixel bounds."""
from pathlib import Path
import numpy as np
from PIL import ImageFont

FONT_PATHS = [Path('C:/Windows/Fonts/arial.ttf'), Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'), Path('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf')]

def text_style(rgb, box):
    x, y = max(0, box['x']), max(0, box['y'])
    crop = rgb[y:min(rgb.shape[0], y+box['height']), x:min(rgb.shape[1], x+box['width'])]
    if crop.size == 0:
        return {}
    colors, counts = np.unique(crop.reshape(-1, 3), axis=0, return_counts=True)
    background = colors[counts.argmax()]
    mask = np.linalg.norm(crop.astype(float)-background.astype(float), axis=2) > 35
    if not mask.any():
        return {}
    ink, occurrences = np.unique(crop[mask], axis=0, return_counts=True)
    foreground = ink[occurrences.argmax()]
    ys, xs = np.where(mask)
    width, height = int(xs.max()-xs.min()+1), int(ys.max()-ys.min()+1)
    font_path = next((p for p in FONT_PATHS if p.is_file()), None)
    size = max(8, round(height*1.3))
    if font_path and box.get('text'):
        best = float('inf')
        for candidate in range(max(5, height//2), min(200, height*3)+1):
            bounds = ImageFont.truetype(str(font_path), candidate).getbbox(box['text'])
            measured_w, measured_h = bounds[2]-bounds[0], bounds[3]-bounds[1]
            loss = abs(measured_w-width)/max(1,width)+abs(measured_h-height)/max(1,height)
            if loss < best:
                best, size = loss, candidate
    return {'color': '#' + ''.join(f'{int(v):02x}' for v in foreground), 'font_size': size}
