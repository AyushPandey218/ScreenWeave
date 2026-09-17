# ScreenWeave implementation plan

## Release contract

Users upload a PNG/JPEG screenshot, reconstruct a supported static interface, correct it, preview it in a sandbox, and download either HTML/CSS/assets or a runnable React/TypeScript/Vite project. Both export formats are required for the planned release.

## Architecture

Vercel serves the frontend. Render serves the FastAPI API. Inference placement is provisional until benchmarks pass. Training runs locally on the RTX 4060; deployed use must not require that machine. No paid API dependency is allowed.

Pipeline: image validation → normalization → OCR and UI detection → hierarchy/style inference → versioned layout JSON → export generators → preview.

## Feasibility gate

- Measure candidate OCR and detector combinations on representative login and landing-page screenshots.
- Record peak process memory, cold/warm latency, text accuracy, and detection quality.
- Repeat requests to detect memory growth.
- Test the deployed service with the development machine off.
- Do not claim free Render suitability before measurements.
- If candidates do not fit, document alternatives and settle the inference architecture before investing in the editor.

## Shared layout format

Versioned document with viewport dimensions and a tree of elements. Each element has a stable ID, type, bounding box, text, style, optional local asset reference, children, and optional detection confidence. Store source dimensions so coordinates remain interpretable.

Start with explicit positioning as a baseline. Infer rows/columns and generate Flexbox/Grid only when grouping is supported. Crop source-image regions for bitmap assets.

## Editor behavior

Properties editing changes layout JSON and regenerates code. Direct source editing enters custom-code mode; arbitrary code is not parsed back into the layout. Resetting to generated code requires an explicit user action and explains loss of custom changes.

## Security and reliability

Validate actual image format, byte size, dimensions, and decompression limits. Bound concurrency. Remove temporary images. Escape extracted text. Preview generated output in a sandbox without scripts. Do not embed secrets or accept arbitrary server-side URLs. First release requires no permanent image storage.

## Evaluation

Compare image-processing and trained-detector baselines, coordinate and inferred layouts, and original/optimized models. Split data by template family. Measure detection precision/recall and localization, OCR accuracy, geometry errors, visual similarity at a fixed viewport, runtime, memory, and human correction effort. Set numeric targets after initial baseline measurements. Verify dataset, font, asset, and model licenses.

## Order of work

1. Hosting skeleton and honest capability endpoint.
2. Image validation, benchmark fixtures, and OCR/detector experiments.
3. Shared layout schema and HTML/CSS generator.
4. ML baseline comparison and deployment gate.
5. Frontend workspace and properties editor.
6. React/TypeScript export with a build verification of exported projects.
7. Code editing, isolated preview, downloads, and error states.
8. Final deployment, usability checks, and academic documentation.

## Deferred

Accounts, cloud history, drag-and-drop editing, automatic visual correction, complex dashboards, multi-page projects, and responsive inference. Do not expand these until the release contract is met.
