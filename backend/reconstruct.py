"""Experimental fixed-viewport reconstruction, using OCR and contour heuristics."""
import argparse
import html
import io
import json
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

from app.baseline import inspect_image
from app.shapes import detect_shapes
from app.typography import text_style
from react_export import write_react_project


def color(pixels):
    values, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    return "#" + "".join(f"{int(v):02x}" for v in values[counts.argmax()])


def contains(parent, child):
    return (parent["x"] <= child["x"] and parent["y"] <= child["y"]
            and parent["x"] + parent["width"] >= child["x"] + child["width"]
            and parent["y"] + parent["height"] >= child["y"] + child["height"])


def reconstruct(payload):
    inspect_image(payload)  # Enforce the existing image safety limits.
    rgb = np.asarray(Image.open(io.BytesIO(payload)).convert("RGB"))
    height, width = rgb.shape[:2]
    # Bound the detector's tensor size; RapidOCR maps boxes back to source pixels.
    engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1,
                      max_side_len=960, det_limit_side_len=960, det_limit_type="max")
    found, _ = engine(payload, use_cls=False)
    texts = []
    for polygon, value, confidence in found or []:
        points = np.array(polygon)
        x, y = points.min(axis=0)
        right, bottom = points.max(axis=0)
        texts.append({"x": int(x), "y": int(y), "width": int(right-x), "height": int(bottom-y), "text": value, "confidence": float(confidence)})
    for text in texts:
        text.update(text_style(rgb, text))
    boxes = detect_shapes(rgb, texts)
    elements = []
    consumed = set()
    for index, box in enumerate(boxes):
        x, y, w, h = (box[k] for k in ("x", "y", "width", "height"))
        labels = [(i, t) for i, t in enumerate(texts) if contains(box, t)]
        nested = any(contains(box, other) and other is not box and "src" not in other for other in boxes)
        kind = "image" if "src" in box else "container" if nested or h > 100 else "button" if labels else "input"
        element = {**box, "id": f"element-{index}", "type": kind}
        if kind in {"button", "image"}:
            element["text"] = " ".join(t["text"] for _, t in labels)
            consumed.update(i for i, _ in labels)
        if kind == "button" and labels:
            element.update({key: labels[0][1][key] for key in ("color", "font_size") if key in labels[0][1]})
        parents = [e for e in elements if e["type"] == "container" and contains(e, box)]
        element["parent_id"] = min(parents, key=lambda e: e["width"]*e["height"])["id"] if parents else None
        elements.append(element)
    for i, text in enumerate(texts):
        if i in consumed:
            continue
        parents = [e for e in elements if e["type"] == "container" and contains(e, text)]
        elements.append({**text, "id": f"text-{i}", "type": "text", "parent_id": min(parents, key=lambda e: e["width"]*e["height"])["id"] if parents else None})
    return {"version": 1, "viewport": {"width": width, "height": height}, "background": color(rgb), "elements": elements, "limitations": ["Heuristic labels, not a trained UI detector", "Fixed viewport; no responsive inference", "Fonts, borders, and corner radii are estimates", "Small detected graphics are embedded PNG crops, not editable vectors", "No working authentication"]}


def export(layout):
    rules = ["*{box-sizing:border-box}", f"body{{margin:0;background:{layout['background']};font-family:Arial,sans-serif}}", f".page{{position:relative;width:{layout['viewport']['width']}px;height:{layout['viewport']['height']}px}}"]
    markup = []
    for e in layout["elements"]:
        identity = e["id"]
        rules.append(f"#{identity}{{position:absolute;left:{e['x']}px;top:{e['y']}px;width:{e['width']}px;height:{e['height']}px;}}")
        if e["type"] == "image":
            markup.append(f'<img id="{identity}" src="{html.escape(e["src"], quote=True)}" alt="Reconstructed graphic">')
        elif e["type"] == "text":
            rules.append(f"#{identity}{{font-size:{e.get('font_size', round(e['height']*0.95))}px;line-height:1;white-space:nowrap;color:{e.get('color', '#172554')}}}")
            markup.append(f'<div id="{identity}">{html.escape(e["text"])}</div>')
        else:
            radius = "50%" if e.get("geometry") == "ellipse" else f"{e['radius']}px"
            rules.append(f"#{identity}{{background:{e['background']};border:{e.get('border_width', 1)}px solid {e['border']};border-radius:{radius};padding:0}}")
            if e["type"] == "button":
                rules.append(f"#{identity}{{color:{e.get('color', '#ffffff')};font:{e.get('font_size', 20)}px Arial,sans-serif}}")
                markup.append(f'<button type="button" id="{identity}">{html.escape(e.get("text", ""))}</button>')
            elif e["type"] == "input":
                markup.append(f'<input id="{identity}" aria-label="Reconstructed input" autocomplete="off">')
            else:
                markup.append(f'<div id="{identity}" aria-hidden="true"></div>')
    document = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ScreenWeave reconstruction</title><link rel="stylesheet" href="styles.css"></head><body><main class="page">' + "\n".join(markup) + '</main></body></html>'
    return document, "\n".join(rules)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reports/reconstruction/login"))
    args = parser.parse_args()
    start = time.perf_counter()
    layout = reconstruct(args.input.read_bytes())
    document, css = export(layout)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
    (args.output / "index.html").write_text(document, encoding="utf-8")
    (args.output / "styles.css").write_text(css, encoding="utf-8")
    write_react_project(layout, css, args.output / "react")
    print(json.dumps({"seconds": round(time.perf_counter()-start, 3), "elements": [{"type": e["type"], "text": e.get("text")} for e in layout["elements"]]}))
