"""Conservative rectangular media detection before individual contour extraction."""
import base64
import io
import cv2
import numpy as np
from PIL import Image


def image_source(crop):
    image = Image.fromarray(crop)
    # Keep assets within the editor/export schema's 200,000-character limit.
    while True:
        stream = io.BytesIO()
        image.save(stream, format='PNG', optimize=True)
        encoded = base64.b64encode(stream.getvalue()).decode('ascii')
        if len(encoded) <= 199970:
            return 'data:image/png;base64,' + encoded
        image = image.resize((max(1, int(image.width*.8)), max(1, int(image.height*.8))), Image.Resampling.LANCZOS)


def textured(crop, minimum_colors=45):
    sample = cv2.resize(crop, (64, 64), interpolation=cv2.INTER_AREA)
    quantized = sample // 24
    _, counts = np.unique(quantized.reshape(-1, 3), axis=0, return_counts=True)
    gray = cv2.cvtColor(sample, cv2.COLOR_RGB2GRAY)
    _, tones = np.unique(gray//8, return_counts=True)
    gray_detail = len(tones) >= 12 and tones.max()/4096 < .35 and np.mean(cv2.Canny(gray, 20, 80)>0) > .08
    return (len(counts) >= minimum_colors and counts.max()/4096 < .65) or gray_detail


def detect_media(rgb, texts):
    height, width = rgb.shape[:2]
    scale = min(1., 1200/max(height, width))
    small = cv2.resize(rgb, (round(width*scale), round(height*scale)))
    edges = cv2.Canny(cv2.cvtColor(small, cv2.COLOR_RGB2GRAY), 20, 80)
    # A second mask finds rectangular photos whose internal edges are disconnected.
    colors, counts = np.unique(small[::4, ::4].reshape(-1, 3)//8, axis=0, return_counts=True)
    background = colors[counts.argmax()].astype(float)*8+4
    foreground = (np.linalg.norm(small.astype(float)-background, axis=2)>24).astype('uint8')*255
    candidates = []
    for mask in (edges, foreground):
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            sx, sy, sw, sh = cv2.boundingRect(contour)
            x,y,w,h = [round(n/scale) for n in (sx,sy,sw,sh)]
            w,h = min(w,width-x), min(h,height-y)
            if w < 100 or h < 70 or w*h < 10000 or w*h > width*height*.95:
                continue
            if cv2.contourArea(contour)/(sw*sh) < .80:
                continue
            crop = rgb[y:y+h,x:x+w]
            if not textured(crop):
                continue
            # Photographic detail must cover most of the region, not just one icon.
            cells = [crop[round(j*h/4):round((j+1)*h/4),round(i*w/4):round((i+1)*w/4)] for j in range(4) for i in range(4)]
            if sum(textured(cell, 24) for cell in cells) < 8:
                continue
            candidates.append({'x':x,'y':y,'width':w,'height':h})
    selected = []
    for box in sorted(candidates, key=lambda b:-b['width']*b['height']):
        if any(intersection(box,p)/min(box['width']*box['height'],p['width']*p['height'])>.8 for p in selected):
            continue
        x,y,w,h = [box[k] for k in ('x','y','width','height')]
        selected.append({**box,'src':image_source(rgb[y:y+h,x:x+w]),'radius':0,'background':'#ffffff','border':'#ffffff','border_width':0})
        if len(selected) == 20:
            break
    return selected


def intersection(a,b):
    return max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x']))*max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']))
