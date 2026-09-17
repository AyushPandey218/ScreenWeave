"""Estimate rounded geometry; preserve unrecognized small graphics as PNG crops."""
import base64
import io

import cv2
import numpy as np
from PIL import Image


def dominant(pixels):
    values, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    return "#" + "".join(f"{int(v):02x}" for v in values[counts.argmax()])


def rounded_mask(width, height, radius):
    yy, xx = np.mgrid[:height, :width]
    dx = np.maximum(np.maximum(radius - xx, xx - (width - 1 - radius)), 0)
    dy = np.maximum(np.maximum(radius - yy, yy - (height - 1 - radius)), 0)
    return (dx * dx + dy * dy <= radius * radius).astype(np.uint8)


def fit_geometry(contour):
    x, y, width, height = cv2.boundingRect(contour)
    scale = min(1.0, 512 / max(width, height))
    w, h = max(2, round(width * scale)), max(2, round(height * scale))
    full = np.zeros((height, width), np.uint8)
    cv2.drawContours(full, [contour - [x, y]], -1, 1, cv2.FILLED)
    target = cv2.resize(full, (w, h), interpolation=cv2.INTER_NEAREST)
    best = (0.0, 0, "rounded-rectangle")
    for radius in range(min(w, h) // 2 + 1):
        mask = rounded_mask(w, h, radius)
        union = np.count_nonzero(mask | target)
        score = np.count_nonzero(mask & target) / max(1, union)
        if score > best[0]:
            best = (score, round(radius / scale), "rounded-rectangle")
    ellipse = np.zeros_like(target)
    cv2.ellipse(ellipse, ((w-1)//2, (h-1)//2), (max(1,(w-1)//2), max(1,(h-1)//2)), 0, 0, 360, 1, -1)
    score = np.count_nonzero(ellipse & target) / max(1, np.count_nonzero(ellipse | target))
    if score > best[0] + 0.015:
        best = (score, min(width, height) // 2, "ellipse")
    return best


def overlap(a, b):
    return max(0, min(a['x']+a['width'], b['x']+b['width'])-max(a['x'], b['x'])) * max(0, min(a['y']+a['height'], b['y']+b['height'])-max(a['y'], b['y']))


def detect_shapes(rgb, texts):
    edges = cv2.Canny(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), 20, 80)
    # Bridge one-pixel gaps caused by antialiased/thin curved borders.
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for index, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        if w < 10 or h < 10:
            continue
        box = {"x": x, "y": y, "width": w, "height": h}
        # Do not mistake text glyphs or whole words for controls/icons.
        if any(overlap(box, t) / (w*h) > 0.45 for t in texts):
            continue
        if w > 96 or h > 96:
            if w < 60 or h < 22:
                continue
        score, radius, geometry = fit_geometry(contour)
        if score < 0.94 and (w > 96 or h > 96):
            continue
        candidates.append({**box, "radius": radius, "geometry": geometry,
                           "shape_score": round(score, 3), "contour": contour, "index": index})
    candidates.sort(key=lambda c: -(c['width']*c['height']))
    selected = []
    accepted_indices = set()
    for candidate in candidates:
        if any(max(abs(candidate[k]-b[k]) for k in ('x', 'y', 'width', 'height')) <= 4 for b in selected):
            continue
        # Keep a small icon as one graphic instead of exporting its internal edges.
        ancestor = int(hierarchy[0][candidate['index']][3])
        skip = False
        while ancestor >= 0:
            if ancestor in accepted_indices:
                parent = next(b for b in selected if b['index'] == ancestor)
                if parent['width'] <= 96 and parent['height'] <= 96:
                    skip = True
                    break
            ancestor = int(hierarchy[0][ancestor][3])
        if skip:
            continue
        x, y, w, h = (candidate[k] for k in ('x', 'y', 'width', 'height'))
        mask = np.zeros((h, w), np.uint8)
        cv2.drawContours(mask, [candidate['contour'] - [x, y]], -1, 255, -1)
        interior = cv2.erode(mask, np.ones((7, 7), np.uint8)) > 0
        crop = rgb[y:y+h, x:x+w]
        candidate['background'] = dominant(crop[interior] if interior.any() else crop)
        # A narrow ring just inside the detected contour usually captures its stroke.
        ring = (mask > 0) & ~interior
        background_rgb = np.array([int(candidate['background'][i:i+2], 16) for i in (1, 3, 5)])
        stroke = crop[ring]
        contrasting = stroke[np.linalg.norm(stroke.astype(float) - background_rgb, axis=1) > 18]
        candidate['border'] = dominant(contrasting) if len(contrasting) else candidate['background']
        if w <= 96 and h <= 96:
            # Preserve the exact curve/details. This is a raster asset, not editable vector geometry.
            buffer = io.BytesIO()
            Image.fromarray(crop).save(buffer, format='PNG')
            candidate['src'] = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
        selected.append(candidate)
        accepted_indices.add(candidate['index'])
    return [{k: v for k, v in candidate.items() if k not in ('contour', 'index')} for candidate in selected]
