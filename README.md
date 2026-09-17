# ScreenWeave

AI-assisted screenshot reconstruction into editable websites.

## Agreed scope

- Solo MCA AI/ML project using free tools and services.
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

React, Vite, TypeScript, Tailwind CSS, Monaco Editor; Python, FastAPI, OpenCV, Pillow; PyTorch for training and potentially ONNX Runtime for deployment. Model and OCR choices remain subject to resource and license checks. Accounts and Supabase persistence are deferred.

## Current status

Backend hosting scaffold and an experimental command-line screenshot-to-HTML/CSS
pipeline are implemented. One synthetic login screenshot has been reconstructed
and rendered in a browser. React/TypeScript export now builds and renders too.
The local web upload workflow now supports original/preview comparison, HTML/CSS
viewing, and both ZIP exports. A trained UI detector and public deployment remain
unimplemented or unvalidated. Element property editing is available; direct
source-code editing is not available yet.

## Element editing

After reconstructing, click an element in the preview or choose it from the
Edit elements list. Change position, dimensions, text/font, fill/text/border
colors, border width, and corner radius where applicable. Small raster graphics
support position and size changes only. Changes regenerate the preview and both
ZIP exports automatically after a short debounce. Downloads are disabled while
edits are pending or failed, with a retry action for failed updates.

Edits live in the current browser session and are cleared by refresh or replacing
the screenshot. Containers do not move their children: coordinates remain
absolute. The preview uses selection overlays outside a script-disabled iframe;
editor outlines are not included in exported files.

`POST /render` accepts the edited layout and validates IDs, dimensions, colors,
and supported properties before regenerating HTML/CSS and React. It does not
rerun OCR. The frontend build, 12 backend tests, browser editing/download/error
checks, and a build of the downloaded edited React project pass locally.

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
landing-page reconstruction. Public deployment is still untested.

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
Docker is not installed locally, so its build and hosted behavior are unverified.
`frontend/vercel.json` specifies the Vite build/output configuration.

Run `python backend/benchmark_service.py` to measure an isolated real HTTP server
including OCR, geometry detection, and both ZIP exports. It writes
`reports/service-benchmark.json`; measurements cover the Windows process tree
(including the server behind the virtualenv launcher). They are not Render
hardware measurements. OCR's internal image is now capped at a 960px long side
to reduce peak memory; returned geometry still uses source-image coordinates.
Small text in large images may lose accuracy at this resolution.
