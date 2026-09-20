import type {Element, Layout} from './ElementEditor';
export type Region = {x:number; y:number; width:number; height:number};
export function inside(e: Region, r: Region) {
  return e.x >= r.x && e.y >= r.y && e.x + e.width <= r.x + r.width && e.y + e.height <= r.y + r.height;
}
export function mergeRegion(layout: Layout, region: Region, patch: Layout): Layout {
  if (![region.x,region.y,region.width,region.height].every(Number.isFinite) || region.x<0 || region.y<0 || region.width<1 || region.height<1 || region.x+region.width>layout.viewport.width || region.y+region.height>layout.viewport.height) throw new Error('Region must fit within the screenshot.');
  if (patch.viewport.width!==region.width || patch.viewport.height!==region.height) throw new Error('The returned crop dimensions do not match the selection.');
  if (!patch.elements.length) throw new Error('No elements were found. Try a larger region.');
  const removed = new Set(layout.elements.filter(e => inside(e,region)).map(e => e.id));
  const kept = layout.elements.filter(e => !removed.has(e.id));
  if (kept.length + patch.elements.length > 500) throw new Error('This result would exceed 500 elements.');
  const ids = new Map(patch.elements.map(e => [e.id, 'region-' + crypto.randomUUID()]));
  const additions: Element[] = patch.elements.map(e => {
    const x = Math.max(0,Math.min(region.width-1,e.x)), y = Math.max(0,Math.min(region.height-1,e.y));
    const placed = {...e,id:ids.get(e.id)!,x:region.x+x,y:region.y+y,width:Math.min(e.width,region.width-x),height:Math.min(e.height,region.height-y)};
    const parent = kept.filter(k => k.type==='container' && inside(placed,k)).sort((a,b)=>a.width*a.height-b.width*b.height)[0];
    return {...placed,parent_id:(e.parent_id && ids.get(e.parent_id)) || parent?.id || null};
  });
  // Preserve all outside elements and their relative order.
  const elements: Element[] = [];
  let inserted = false;
  for (const e of layout.elements) {
    if (removed.has(e.id)) {
      if (!inserted) {elements.push(...additions);inserted=true;}
    } else elements.push(removed.has(e.parent_id || '') ? {...e,parent_id:null} : e);
  }
  if (!inserted) elements.push(...additions);
  const next = {...layout,elements};
  if (new TextEncoder().encode(JSON.stringify(next)).length > 5*1024*1024) throw new Error('The resulting layout is too large. Try a smaller region.');
  return next;
}
