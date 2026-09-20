import type {Element, Layout} from './ElementEditor';
import type {Project} from './projects';

const MAX_BYTES = 25 * 1024 * 1024;
const colorPattern = /^#[0-9a-fA-F]{6}$/;
const idPattern = /^[a-zA-Z][a-zA-Z0-9_-]{0,79}$/;
const pngPattern = /^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/;
function check(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
function object(value: unknown): Record<string, unknown> {
  check(value !== null && typeof value === 'object' && !Array.isArray(value), 'Invalid project structure.');
  return value as Record<string, unknown>;
}
function number(value: unknown, min: number, max: number): number {
  check(typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max, 'Invalid element dimensions or styles.');
  return value;
}
function color(value: unknown): string {
  check(typeof value === 'string' && colorPattern.test(value), 'Invalid project color.');
  return value;
}
function layout(value: unknown): Layout {
  const data = object(value), viewport = object(data.viewport);
  check(data.version === 1, 'This layout version is not supported.');
  const width = number(viewport.width, 1, 10000), height = number(viewport.height, 1, 10000);
  check(Number.isInteger(width) && Number.isInteger(height) && width * height <= 4000000, 'Invalid project viewport.');
  check(Array.isArray(data.elements) && data.elements.length <= 500, 'Projects support up to 500 elements.');
  const ids = new Set<string>();
  const elements: Element[] = data.elements.map(raw => {
    const e = object(raw);
    check(typeof e.id === 'string' && idPattern.test(e.id) && !ids.has(e.id), 'Invalid or duplicate element ID.');
    ids.add(e.id);
    check(typeof e.type === 'string' && ['text','button','input','container','image'].includes(e.type), 'Unsupported element type.');
    const item: Element = {id:e.id, type:e.type, x:number(e.x,0,10000), y:number(e.y,0,10000), width:number(e.width,Number.MIN_VALUE,10000), height:number(e.height,Number.MIN_VALUE,10000)};
    for (const key of ['text','parent_id'] as const) {
      if (e[key] == null) continue;
      check(typeof e[key] === 'string' && (key === 'text' ? e[key].length <= 10000 : idPattern.test(e[key])), 'Invalid element text or parent.');
      item[key] = e[key];
    }
    for (const key of ['background','border','color'] as const) if (e[key] != null) item[key] = color(e[key]);
    if (e.radius != null) item.radius = number(e.radius,0,5000);
    if (e.border_width != null) item.border_width = number(e.border_width,0,50);
    if (e.font_size != null) item.font_size = number(e.font_size,1,500);
    if (e.geometry != null) {
      check(e.geometry === 'ellipse' || e.geometry === 'rounded-rectangle', 'Invalid element geometry.');
      item.geometry = e.geometry;
    }
    if (item.type === 'image') {
      check(typeof e.src === 'string' && e.src.length <= 200000 && pngPattern.test(e.src), 'Invalid embedded image.');
      item.src = e.src;
    }
    return item;
  });
  const limitations = data.limitations ?? [];
  check(Array.isArray(limitations) && limitations.length <= 20 && limitations.every(v => typeof v === 'string' && v.length <= 2000), 'Invalid layout notes.');
  const result: Layout = {version:1, viewport:{width,height}, background:color(data.background), elements, limitations};
  check(new TextEncoder().encode(JSON.stringify(result)).length <= 5 * 1024 * 1024, 'This layout is too large to render.');
  return result;
}
export function parseProjectBackup(text: string): Omit<Project, 'id' | 'updatedAt'> {
  check(new TextEncoder().encode(text).length <= MAX_BYTES, 'Choose a backup under 25 MiB.');
  let parsed: unknown;
  try {parsed = JSON.parse(text);} catch {throw new Error('This file is not a valid ScreenWeave backup.');}
  const data = object(parsed);
  check(data.format === 'screenweave-project' && data.version === 1, 'Choose a ScreenWeave project backup (version 1).');
  const p = object(data.project);
  check(typeof p.name === 'string' && p.name.trim().length > 0 && p.name.length <= 100, 'Invalid project name.');
  check(typeof p.source === 'string' && p.source.length <= 7 * 1024 * 1024 && /^data:image\/(png|jpeg);base64,[A-Za-z0-9+/]+={0,2}$/.test(p.source), 'Invalid reference screenshot.');
  const current = layout(p.layout), original = layout(p.original);
  check(current.viewport.width === original.viewport.width && current.viewport.height === original.viewport.height, 'Project viewport sizes do not match.');
  return {name:p.name.trim(), source:p.source, layout:current, original};
}
export function downloadBackup(project: Project) {
  const text = JSON.stringify({format:'screenweave-project', version:1, project:{name:project.name, source:project.source, layout:project.layout, original:project.original}});
  const blob = new Blob([text], {type:'application/json'});
  check(blob.size <= MAX_BYTES, 'This project exceeds the 25 MiB backup limit.');
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = (project.name.replace(/[^a-zA-Z0-9_-]+/g,'-').slice(0,60) || 'project') + '.screenweave.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
