import {useEffect, useRef, useState, type PointerEvent} from 'react';
import {createPortal} from 'react-dom';
import {apiRequest, type Result} from './projects';
import {inside, type Region} from './region';
import type {Layout} from './ElementEditor';

type Props = {source:string; layout:Layout; scale:number; artboard:HTMLDivElement|null; onApply:(region:Region,layout:Layout)=>void};
export default function RegionReconstruction({source,layout,scale,artboard,onApply}:Props) {
  const [open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [region,setRegion]=useState<Region>({x:0,y:0,width:Math.min(200,layout.viewport.width),height:Math.min(200,layout.viewport.height)});
  const [result,setResult]=useState<Result|null>(null);
  const controller=useRef<AbortController|null>(null),start=useRef<{x:number;y:number}|null>(null);
  useEffect(()=>()=>{controller.current?.abort();controller.current=null;},[]);
  function close(){controller.current?.abort();controller.current=null;setBusy(false);start.current=null;setOpen(false);setResult(null);setError('');}
  function point(event:PointerEvent<HTMLDivElement>){
    const box=event.currentTarget.getBoundingClientRect();
    return {x:Math.max(0,Math.min(layout.viewport.width,Math.round((event.clientX-box.left)/scale))),y:Math.max(0,Math.min(layout.viewport.height,Math.round((event.clientY-box.top)/scale)))};
  }
  function draw(event:PointerEvent<HTMLDivElement>){
    if(!start.current)return;
    const p=point(event),x=Math.min(layout.viewport.width-1,p.x,start.current.x),y=Math.min(layout.viewport.height-1,p.y,start.current.y);
    setRegion({x,y,width:Math.min(layout.viewport.width-x,Math.max(1,Math.abs(p.x-start.current.x))),height:Math.min(layout.viewport.height-y,Math.max(1,Math.abs(p.y-start.current.y)))});
  }
  function update(key:keyof Region,value:number){
    if(!Number.isFinite(value))return;
    const next={...region,[key]:Math.round(value)};
    next.x=Math.max(0,Math.min(layout.viewport.width-1,next.x));
    next.y=Math.max(0,Math.min(layout.viewport.height-1,next.y));
    next.width=Math.max(1,Math.min(layout.viewport.width-next.x,next.width));
    next.height=Math.max(1,Math.min(layout.viewport.height-next.y,next.height));
    setRegion(next);
  }
  async function reconstruct(){
    if(busy)return;
    setBusy(true);setError('');setResult(null);
    const c=new AbortController();controller.current=c;
    const timeout=setTimeout(()=>c.abort(),180000);
    try {
      const bitmap=await createImageBitmap(await(await fetch(source)).blob());
      let crop:Blob;
      try{
        const canvas=document.createElement('canvas');canvas.width=region.width;canvas.height=region.height;
        const context=canvas.getContext('2d');if(!context)throw new Error('Could not prepare the selected region.');
        context.drawImage(bitmap,region.x,region.y,region.width,region.height,0,0,region.width,region.height);
        crop=await new Promise<Blob>((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('Could not crop screenshot.')),'image/png'));
      }finally{bitmap.close();}
      if(c.signal.aborted)throw new Error('Request cancelled.');
      if(crop.size>5*1024*1024)throw new Error('This crop is too large. Select a smaller region.');
      const next=await apiRequest('/reconstruct',crop,'image/png',c.signal);
      if(!c.signal.aborted){
        if(!next.layout.elements.length)throw new Error('No elements found. Try a larger region.');
        setResult(next);
      }
    }catch(e){if(controller.current===c)setError(c.signal.aborted?'Request cancelled or timed out. Your edits are unchanged.':e instanceof Error?e.message:'Region reconstruction failed.');}
    finally{clearTimeout(timeout);if(controller.current===c)setBusy(false);}
  }
  const preview=result?.html.replace('<link rel="stylesheet" href="styles.css">',`<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none'"><style>${result.css}</style>`);
  const count=layout.elements.filter(e=>inside(e,region)).length;
  return <div className="region-tools">
    <button aria-expanded={open} onClick={()=>open?close():setOpen(true)}>Reconstruct region</button>
    {open&&<div className="region-panel">
      <p>{result?'Preview the replacement on the canvas. Apply it or discard it.':'Draw a rectangle on the canvas, or enter its bounds below. Uses your original screenshot.'}</p>
      <div className="region-fields">{(['x','y','width','height'] as const).map(key=><label key={key}>{key}<input type="number" aria-label={'Region '+key} value={region[key]} min={key==='x'||key==='y'?0:1} max={key==='x'||key==='width'?layout.viewport.width:layout.viewport.height} disabled={busy||!!result} onChange={e=>update(key,e.target.valueAsNumber)}/></label>)}</div>
      <p className="region-warning">Replaces {count} fully enclosed elements. Elements crossing the border stay unchanged. You can undo after applying.</p>
      <div className="actions">{result?<><button className="primary" onClick={()=>{try{onApply(region,result.layout);close();}catch(e){setError(e instanceof Error?e.message:'Could not apply result.');}}}>Apply region</button><button onClick={()=>{setResult(null);setError('');}}>Discard result</button></>:<button className="primary" disabled={busy||region.width<16||region.height<16} onClick={()=>void reconstruct()}>{busy?'Reconstructing region…':'Reconstruct selection'}</button>}<button onClick={close}>{busy?'Cancel request':'Close region tool'}</button></div>
      {busy&&<p role="status">Processing this crop. The free service may need time to start.</p>}
      {error&&<p role="alert" className="insert-error">{error}</p>}
    </div>}
    {open&&artboard&&createPortal(<div className="region-selection" aria-label="Draw reconstruction region" onPointerDown={event=>{if(busy||result||event.button!==0)return;event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);start.current=point(event);}} onPointerMove={draw} onPointerUp={event=>{draw(event);start.current=null;}} onPointerCancel={()=>{start.current=null;}}>
      <div className="region-box" style={{left:region.x*scale,top:region.y*scale,width:region.width*scale,height:region.height*scale}}>
        {preview&&<iframe title="Region replacement preview" sandbox="" srcDoc={preview} style={{width:region.width,height:region.height,transform:`scale(${scale})`}}/>}
        <span className="region-dimensions">{region.width} × {region.height}</span>
      </div>
    </div>,artboard)}
  </div>;
}
