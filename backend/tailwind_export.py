"""Static Tailwind utility classes so Vite can discover every generated style."""
import json


def apply_tailwind(layout, files):
    def px(value):
        return f"{float(value):g}px"

    classes = {}
    for e in layout["elements"]:
        rules = ["absolute", f"left-[{px(e['x'])}]", f"top-[{px(e['y'])}]",
                 f"w-[{px(e['width'])}]", f"h-[{px(e['height'])}]"]
        if e["type"] == "text":
            rules += [f"text-[length:{px(e.get('font_size', round(e['height']*.95)))}]",
                      "leading-none", "whitespace-nowrap", f"text-[{e.get('color', '#172554')}]"]
        elif e["type"] != "image":
            radius = "50%" if e.get("geometry") == "ellipse" else px(e.get("radius", 0))
            rules += [f"bg-[{e.get('background', '#ffffff')}]", "border-solid",
                      f"border-[{px(e.get('border_width', 1))}]", f"border-[{e.get('border', '#cbd5e1')}]",
                      f"rounded-[{radius}]", "p-0"]
            if e["type"] == "button":
                rules += [f"text-[{e.get('color', '#ffffff')}]", f"[font:{px(e.get('font_size', 20))}_Arial,sans-serif]"]
        classes[e["id"]] = " ".join(rules)
    page = f"relative w-[{px(layout['viewport']['width'])}] h-[{px(layout['viewport']['height'])}]"
    files["src/classes.ts"] = "export const elementClasses: Record<string, string> = " + json.dumps(classes, indent=2) + ";\nexport const pageClasses = " + json.dumps(page) + ";\n"
    files["src/App.tsx"] = files["src/App.tsx"].replace(
        'import layout from "./layout.json";', 'import layout from "./layout.json";\nimport {elementClasses, pageClasses} from "./classes";'
    ).replace('id={element.id}', 'id={element.id} className={elementClasses[element.id]}').replace('className="page"', 'className={pageClasses}')
    # Keep native control defaults consistent with the plain CSS export.
    files["src/styles.css"] = '@import "tailwindcss/theme.css" layer(theme);\n@import "tailwindcss/utilities.css" layer(utilities);\n@source "./classes.ts";\n*{box-sizing:border-box}\nbody{margin:0;font-family:Arial,sans-serif;background:' + layout["background"] + '}\n'
    files["vite.config.ts"] = 'import {defineConfig} from "vite";\nimport tailwindcss from "@tailwindcss/vite";\nexport default defineConfig({plugins:[tailwindcss()]});\n'
    package = json.loads(files["package.json"])
    package["name"] = "screenweave-tailwind-export"
    package["devDependencies"].update({"tailwindcss": "^4.3.0", "@tailwindcss/vite": "^4.3.0"})
    files["package.json"] = json.dumps(package, indent=2)
    files["README.md"] = """# ScreenWeave React + Tailwind export

Run npm install, then npm run dev. Run npm run build for production.
Requires Node.js 20.19+ or 22.12+.

Edit src/classes.ts to change the generated Tailwind utilities and src/layout.json
for text and image content. Geometry in layout.json is a reference snapshot;
classes.ts controls the rendered geometry and styles. Full class names are static
so Tailwind can find them during builds.

Uses Tailwind 4 with the Vite plugin. Preflight is omitted to preserve native
control appearance from the plain HTML export. Layout uses absolute positioning
at the screenshot size; this export does not infer responsive behavior or add
authentication/business logic.
"""
