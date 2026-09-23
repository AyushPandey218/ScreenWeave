"""Create a standalone React project from the shared layout document."""
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def write_react_project(layout: dict, css: str, output: Path, tailwind: bool = False) -> None:
    files = {
        "package.json": json.dumps({
            "name": "screenweave-export", "version": "0.1.0", "private": True,
            "type": "module", "scripts": {"dev": "vite", "build": "tsc --noEmit && vite build", "preview": "vite preview"},
            "dependencies": {"react": "^19.0.0", "react-dom": "^19.0.0"},
            "devDependencies": {"@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "typescript": "~5.9.0", "vite": "^7.0.0"},
            "engines": {"node": "^20.19.0 || >=22.12.0"},
        }, indent=2),
        "tsconfig.json": json.dumps({"compilerOptions": {"target": "ES2022", "lib": ["ES2022", "DOM", "DOM.Iterable"], "module": "ESNext", "moduleResolution": "Bundler", "jsx": "react-jsx", "strict": True, "skipLibCheck": True, "resolveJsonModule": True, "allowSyntheticDefaultImports": True, "noEmit": True}, "include": ["src"]}, indent=2),
        "index.html": '<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ScreenWeave export</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>',
        "src/main.tsx": 'import { StrictMode } from "react";\nimport { createRoot } from "react-dom/client";\nimport App from "./App";\nimport "./styles.css";\ncreateRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);\n',
        "src/App.tsx": '''import layout from "./layout.json";

type Element = {
  id: string;
  type: string;
  text?: string;
  src?: string;
};

export function ReconstructedElement({ element }: { element: Element }) {
  switch (element.type) {
    case "image":
      return <img id={element.id} src={element.src} alt="Reconstructed graphic" />;
    case "input":
      return <input id={element.id} aria-label="Reconstructed input" autoComplete="off" />;
    case "button":
      return <button id={element.id} type="button">{element.text ?? ""}</button>;
    case "text":
      return <div id={element.id}>{element.text ?? ""}</div>;
    default:
      return <div id={element.id} aria-hidden="true" />;
  }
}

export default function App() {
  return <main className="page">{layout.elements.map(element =>
    <ReconstructedElement key={element.id} element={element} />
  )}</main>;
}
''',
        "src/styles.css": css,
        "src/layout.json": json.dumps(layout, indent=2),
        "README.md": "# ScreenWeave React export\n\nRequires Node.js 20.19+ or 22.12+. Run `npm install`, then `npm run dev`. Run `npm run build` for a production build.\n\nEdit `src/layout.json`, `src/App.tsx`, and `src/styles.css`. This is a static reconstruction at the original viewport size. Authentication and other application logic are not included. Text is rendered through React escaping, not raw HTML.\n",
        ".gitignore": "node_modules/\ndist/\n",
    }
    if tailwind:
        from tailwind_export import apply_tailwind
        apply_tailwind(layout, files)
    from app.components import componentize
    componentize(layout, files, tailwind)
    output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    with ZipFile(output.parent / f"{output.name}.zip", "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
