"""Estimate text color, size, and regular/bold Arial-compatible weight."""
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [Path('C:/Windows/Fonts/arial.ttf'), Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'), Path('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf')]
BOLD_PATHS = [Path('C:/Windows/Fonts/arialbd.ttf'), Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'), Path('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf')]

FONT_FAMILIES = {
    'sans-serif': (FONT_PATHS, BOLD_PATHS),
    'serif': ([Path('C:/Windows/Fonts/times.ttf'), Path('/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf'), Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf')], [Path('C:/Windows/Fonts/timesbd.ttf'), Path('/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf'), Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf')]),
    'monospace': ([Path('C:/Windows/Fonts/cour.ttf'), Path('/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf'), Path('/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf')], [Path('C:/Windows/Fonts/courbd.ttf'), Path('/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf'), Path('/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf')]),
}

@lru_cache(maxsize=128)
def reference_font(path, size):
    return ImageFont.truetype(path, size)

def text_style(rgb, box):
    x, y = max(0, int(box['x'])), max(0, int(box['y']))
    crop = rgb[y:min(rgb.shape[0], y+int(box['height'])), x:min(rgb.shape[1], x+int(box['width']))]
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
    family = 'sans-serif'
    size, weight = max(8, round(height*1.3)), 400
    text = box.get('text', '')
    if text:
        target = Image.fromarray((mask[ys.min():ys.max()+1,xs.min():xs.max()+1]*255).astype('uint8')).resize((96,32))
        target = np.asarray(target)/255.0
        best = float('inf')
        for candidate_family, (regular,bold) in FONT_FAMILIES.items():
            for candidate_weight, paths in ((400,regular),(700,bold)):
                path = next((p for p in paths if p.is_file()), None)
                if path is None:
                    continue
                candidates = []
                for candidate in range(max(5,height//2), min(200,height*3)+1):
                    font = reference_font(str(path), candidate)
                    bounds = font.getbbox(text)
                    w,h = bounds[2]-bounds[0],bounds[3]-bounds[1]
                    if w <= 0 or h <= 0:
                        continue
                    loss = abs(w-width)/max(1,width)+abs(h-height)/max(1,height)
                    candidates.append((loss,candidate,bounds))
                for loss,candidate,bounds in sorted(candidates)[:3]:
                    sample = Image.new('L',(bounds[2]-bounds[0],bounds[3]-bounds[1]),0)
                    ImageDraw.Draw(sample).text((-bounds[0],-bounds[1]),text,font=reference_font(str(path),candidate),fill=255)
                    threshold = 255 * 35 / max(36, float(np.linalg.norm(foreground.astype(float)-background.astype(float))))
                    binary = Image.fromarray((np.asarray(sample) > threshold).astype('uint8')*255)
                    pixels = np.asarray(binary.resize((96,32)))/255.0
                    # Ink density and glyph silhouette distinguish regular from bold.
                    loss += 1.5*abs(pixels.mean()-target.mean()) + .5*np.abs(pixels-target).mean()
                    if loss < best:
                        best,size,weight,family = loss,candidate,candidate_weight,candidate_family
    return {'color':'#'+''.join(f'{int(v):02x}' for v in foreground), 'font_size':size, 'font_weight':weight, 'font_family':family}
