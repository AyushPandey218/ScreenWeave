# ScreenWeave

AI-assisted screenshot reconstruction into editable websites.

## Agreed scope

- Fully hosted operation: Vercel frontend and Render backend; no dependency on the developer's laptop.
- Initial inputs: desktop login screens and simple landing pages.
- Detect text, buttons, inputs, images, cards, and containers.
- Review and edit a reconstruction, then export HTML/CSS or a React + TypeScript Vite project.
- A screenshot provides appearance, not authentication, payment processing, or other backend behavior.

## Milestones

1. Validate hosted resource limits with representative images and candidate OCR/detection engines.
2. Implement a measurable reconstruction baseline and shared layout format.
3. Train and evaluate a lightweight UI detector using template-family-separated data splits.
4. Build upload, comparison, properties editing, code editing, preview, and both export formats.
5. Improve layout inference and evaluate visual quality, memory, latency, and correction effort.
6. Verify public deployment and complete the academic report and demo.

## Stack

React 19, Vite, TypeScript, and custom CSS; Python, FastAPI, OpenCV,
Pillow, RapidOCR, and ONNX Runtime. The current reconstruction pipeline uses OCR
and geometry heuristics. A trained UI detector remains future work.

## Current status

The initial app is deployed on Vercel and Render and was verified by the owner.
The redesign adds Home, Projects, New project, Examples, Help, and dedicated
editor routes. Projects and source screenshots autosave in IndexedDB in the
current browser. They survive refresh, but clearing site data removes them;
they do not sync across devices or deployment domains.

## Element editing

Select an element on the canvas or in Layers. Drag it to move, use its corner
handle to resize, or edit position, dimensions, text, font size, colors, border,
and corner radius in Properties. The workspace includes zoom/fit, a source
reference, duplicate, delete, reset, and undo/redo. Ctrl/Cmd+Z undoes changes;
Ctrl/Cmd+Shift+Z redoes them.

Changes regenerate the preview and HTML/CSS and React ZIP exports after a short
debounce. Downloads remain disabled while rendering is pending or failed.
HTML and CSS tabs are read-only; direct code editing remains future work.
Containers do not move their children: exported coordinates remain absolute.
Preview selection outlines are not included in exports.

Reconstruction now estimates text color and font size from source pixels using
an Arial-compatible reference font, alongside rounded-shape fitting and small
graphic crops. Exact fonts, shadows, complex illustrations, responsive layout
inference, and reliable reconstruction of arbitrary screens remain open work.

Local validation for this update includes 14 backend tests, the frontend
production build, and browser checks for navigation, editing, project
persistence, downloads, and a mobile editor without horizontal overflow.
The browser smoke script is frontend/test-editor.cjs and requires running local
frontend and backend servers plus Playwright.

See [the implementation plan](docs/PLAN.md) for decisions and acceptance criteria.
## Local feasibility benchmark

```sh
pip install -r backend/requirements-benchmark.txt
python backend/benchmark.py
```

Results and synthetic input/detection images are written to `reports/baseline/`.
The first run processed four synthetic fixtures 21 times each, with warm median
latencies of approximately 3–19 ms and sampled process peak RSS of 102 MiB on
the development Windows machine. These are not Render measurements. The process
includes fixture and visualization overhead, but not the API server or OCR/model
inference. Sampling can miss transient memory peaks.

The baseline finds three separate controls in a flat login fixture but only the
outer card in its nested counterpart. It is a geometry experiment, not a usable
reconstruction engine. OCR, semantic detection, real screenshot evaluation, and
hosted resource measurements remain necessary. Invalid, empty, oversized-byte,
and oversized-dimension inputs were rejected successfully.

## OCR experiment

Use a separate virtual environment for this experiment because RapidOCR depends
on `opencv-python`, whereas the geometry benchmark lists the headless variant.
Both packages provide the same `cv2` module and should not be installed together.

```sh
pip install -r backend/requirements-ocr.txt
python backend/benchmark_ocr.py
```

On Linux supply an available TrueType font with `--font /path/to/font.ttf`.
Inputs, ground-truth text boxes, OCR polygons/confidences, annotated images, and
measurements are written to `reports/ocr/`. The experiment runs CPU inference
with two intra-operation threads and orientation classification disabled.

The first local run matched 11 of 12 synthetic text lines exactly. Login and
small low-contrast fixtures had zero character errors; the landing fixture had
one character error. A blank image produced no detections. Warm medians were
153–403 ms for text-containing fixtures, with approximately 343 MiB sampled
process peak RSS. Initialization took approximately 670 ms. Sampling may miss
transient peaks; these measurements exclude an API server and UI detector and
do not establish free Render suitability. Six calls per fixture are only a
short stability check, not a memory-leak or load test.

OCR remains experimental. Real screenshots, positional accuracy evaluation,
engine/model license verification, and Linux/hosted measurements remain open.

## First reconstruction prototype

Using the OCR environment, run from the repository root:

```sh
python backend/reconstruct.py reports/ocr/login.png --output reports/reconstruction/login
```

The output contains `layout.json`, `index.html`, `styles.css`, a `react/` project,
and a source-only `react.zip` download. Open the HTML
file in a browser. The generated page uses actual inputs and a button; it does
not place the screenshot behind the page. The CLI accepts other supported images,
but its heuristics have only been checked on this synthetic login example.

OCR text is combined with nested contour detection. Control labels are heuristic:
small empty rectangles become inputs and small labeled rectangles become buttons.
This can misclassify real interfaces. Parent IDs are preserved in layout JSON;
the initial HTML generator uses flat absolute positioning at the source viewport.
Fonts and text colors are approximated. Corner radii are now estimated by fitting
rounded geometry to detected contours; thin curved outlines are connected before
detection. Small detected graphics (up to 96 pixels in each dimension) are
preserved as embedded PNG crops in both HTML and React, rather than replaced with
boxes. They are raster assets, not editable vectors. Disconnected icon parts,
larger graphics, shadows, and asymmetric corner radii can still be imperfect.
Responsive layout inference remains future work.

The React export includes TypeScript components, layout JSON, CSS, a Vite entry
point, package manifest, and setup instructions. Run `npm install` then
`npm run dev` inside its folder. `npm run build` checks TypeScript and produces
the deployable `dist/` directory. It requires Node 20.19+ or 22.12+.

The login export passed a production build, browser rendering without errors,
and editable-input checks. Its unfocused React and HTML previews are pixel-identical
at 900 × 700. The second synthetic landing fixture exports five text elements;
because that fixture has no card or button shapes, it does not validate complex
landing-page reconstruction. The initial hosted upload/edit/export flow was verified by the owner.

Rounded-control regression coverage is in `backend/test_shapes.py`. Run
`python -m unittest test_shapes.py test_api.py` from `backend`. A browser-rendered
fixture is saved as `reports/rounded-controls-source.png`; its reconstructed
preview and exports are in `reports/reconstruction/rounded/`. This checks pill
inputs/buttons, a rounded card, a curved graphic, preservation of square corners,
OCR exclusion, border visibility, and both export paths. The user's exact
screenshot has not yet been tested.

The first local generation took approximately one second. Browser checks found
two inputs and one button. Nested parent relationships and HTML text escaping
passed. `reports/reconstruction/login/preview.png` shows the rendered output;
`verification.json` records checks and a background-dominated pixel difference
metric, which must not be interpreted as general reconstruction accuracy.

## Backend development

Install Python 3.11+, create a virtual environment, then run from `backend`:

```sh
pip install -r requirements-ocr.txt
uvicorn app.main:app --reload
```

`GET /health` reports service status. `GET /capabilities` explicitly lists the currently available features. Configure `ALLOWED_ORIGINS` as a comma-separated list of exact frontend origins before deployment.

`POST /reconstruct` accepts raw PNG/JPEG bytes (not multipart), validates the
5 MiB/4-megapixel limits, and returns layout, HTML, CSS, and base64 ZIP exports.
Only one job runs at a time; other requests receive HTTP 429. Uploaded bytes
are processed in memory; temporary export files are cleaned up after each job.
Use a single Uvicorn worker for this memory-constrained prototype.

## Frontend development

From `frontend`, run `npm install` then `npm run dev`. The local workspace is
available at `http://localhost:5173` and connects to `http://127.0.0.1:8000`.
Set `VITE_API_URL` before building to change the API address (see `.env.example`).
Run `npm run build` for a TypeScript check and production build.

For Vercel, use `frontend` as the root directory, `npm run build` as the build
command, and `dist` as the output directory. Set `VITE_API_URL` to the HTTPS
backend address. Set Render's `ALLOWED_ORIGINS` to the exact Vercel origin.
These settings have not yet been verified on hosted Linux; model memory and
OpenCV system dependencies remain part of the deployment feasibility gate.

Local verification: five API tests cover rejected inputs, byte limits, busy
responses, CORS, and real OCR-to-ZIP processing. Run `python -m unittest test_api.py`
from `backend` with the OCR dependencies and `httpx` installed. Browser checks
cover upload, iframe preview, both downloads, CSS viewing, invalid-file feedback,
stale result clearing, and a 390px mobile layout without horizontal overflow.

The root `render.yaml` is a deployment scaffold. Creating the service in your own hosting account remains a separate step.

See [deployment instructions](docs/DEPLOYMENT.md) for the GitHub → Render/Vercel
setup. Render now uses `backend/Dockerfile` to include OpenCV's Linux libraries.
Docker is not installed locally. The initial hosted Docker service was verified; this update also installs Liberation fonts for typography estimation.
`frontend/vercel.json` specifies the Vite build/output configuration.

Run `python backend/benchmark_service.py` to measure an isolated real HTTP server
including OCR, geometry detection, and both ZIP exports. It writes
`reports/service-benchmark.json`; measurements cover the Windows process tree
(including the server behind the virtualenv launcher). They are not Render
hardware measurements. OCR's internal image is now capped at a 960px long side
to reduce peak memory; returned geometry still uses source-image coordinates.
Small text in large images may lose accuracy at this resolution.

### Compare and complete a draft

In the editor, enable **Compare original** and adjust its opacity to see
differences against the reconstruction. **Selection outlines** can be hidden.
Comparison settings are editor-only and do not change exported code.

Use **Add element** for missing text, buttons, inputs, cards, and images.
New elements are editable, saved locally, and included in undo/redo and exports.
Cards start behind existing layers. Images accept PNG/JPEG under 5 MiB and
4 megapixels, then are resized to at most 512 pixels on their longest side
(and further if needed) to fit the embedded PNG size limit.
The layout supports at most 500 elements.

Run frontend/test-tools.cjs with Playwright and local servers to check these
features, exports, reload persistence, and mobile overflow.

### Project backups and alignment

Use **Project backup** in the editor to download a versioned
.screenweave.json file containing the reference, current layout, and original
layout. **Import project** on the Projects page validates the file and restores
a new copy without overwriting existing projects. Backups are limited to 25 MiB;
each layout must fit the existing 5 MiB rendering limit. Undo history and
editor preferences are not included. Backup and import work without the API;
rendering a restored project still requires the backend.

Align the selected element to canvas edges or centers using the Properties
buttons. Enable **Snap to 8 px grid** for drag/resize snapping. Arrow keys on a
focused canvas element move by one pixel; Shift+arrow moves by ten pixels.
Alignment, snapping, and nudges participate in undo/redo. Containers still move
independently of their children.

frontend/test-backup.cjs covers backup/import, invalid files, alignment, nudges,
snapping, undo, and mobile layout using local servers and Playwright.

### Selective reconstruction and Tailwind export

In Canvas, choose **Reconstruct region**, then draw a rectangle or enter its
bounds. **Reconstruct selection** sends only that crop of the original screenshot
to the existing bounded reconstruction endpoint. The result appears as an
isolated preview; **Apply region** replaces only elements fully enclosed by the
selection. Elements crossing its boundary are retained. IDs and parent links
are remapped, and positions are offset back into screenshot coordinates.
Discard/cancel leaves the layout unchanged; applying participates in undo/redo,
autosave, backups, and all exports. The original reset baseline stays unchanged.
A crop can improve small details but is not guaranteed to outperform the
full-image result.

**React + Tailwind** downloads a Vite/React/TypeScript project using Tailwind 4
and its Vite plugin. Full utility names are emitted in src/classes.ts so the
compiler can discover arbitrary pixel/color values. Edit that file for styles
and geometry, and src/layout.json for content. Preflight is omitted to match
the native controls in the HTML export. This remains a fixed-size layout;
responsive inference is not included.

Validation: 15 backend tests, the frontend and downloaded Tailwind production
builds, browser comparison of computed styles against HTML, and region
apply/discard/cancel, preservation of outside edits, undo/redo, reload, and mobile
checks. Run frontend/test-region.cjs with Playwright and local servers.
frontend/test-region-merge.mjs exercises merge edge cases using Node with native
TypeScript stripping (tested on Node 24).

### Editor workspace and quality review

A single **Export** menu contains all code formats and the project backup.
**Hide layers** and **Hide properties** expand the canvas; Show restores them.
Comparison defaults to a draggable before/after divider (original left, draft
right). Overlay mode remains available. Comparison controls never alter exports.

Expand **Quality checks** in Properties to compare a locally rasterized draft
with the reference, sampled at a maximum long side of 960 pixels. The report
counts pixels with mean RGB channel difference above 25/255 and shows a red
difference overlay, high-difference cells in a 4x4 grid, overflow warnings, and
font sizes below 12 px. This is a visual diagnostic, not an accuracy score.
Flat backgrounds, font rendering, antialiasing, and browser rasterization affect
it. Editing the draft invalidates the report. Image comparison runs in the
browser using html-to-image, with a script-disabled isolated render.

Typography now estimates regular/bold weight from reference glyph dimensions,
ink density, and silhouette, using Arial/Liberation Sans. It does not identify
arbitrary font families. Text/button properties include weight, line height,
alignment, and wrapping, all validated and preserved in backups and HTML,
React, and Tailwind exports. Reference fonts use a bounded cache.

Validation includes 18 backend tests, frontend and Tailwind export builds,
browser style parity with HTML, typography backup preservation, and
frontend/test-quality.cjs for the workspace controls and visual reports.

Backend diagnostics are available at /dashboard (the API root redirects there). The public dashboard shows process uptime, memory, aggregate request timings and failures, OCR package availability, and a test upload. Metrics reset on restart; refresh is manual. It never displays uploaded screenshots or private logs.

The editor uses the full viewport with internal panel scrolling. The website navigation is hidden while editing; use Back to Projects to leave. On small screens, layers and properties start collapsed and open over the canvas.
