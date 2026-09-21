import {useEffect,useRef,useState} from 'react';
import type {Layout} from './ElementEditor';
import type {Result} from './projects';

type Report={heatmap:string;difference:number;regions:{x:number;y:number;score:number}[];issues:string[]};
export default function QualityCheck({source,result,layout,disabled,onHeatmap}:{source:string;result:Result|null;layout:Layout;disabled:boolean;onHeatmap:(value:string|null)=>void}){
 const [busy,setBusy]=useState(false),[report,setReport]=useState<Report|null>(null),[error,setError]=useState(''),[show,setShow]=useState(false);
 const generation=useRef(0),frame=useRef<HTMLIFrameElement|null>(null);
 useEffect(()=>{generation.current++;setReport(null);setShow(false);setError('');setBusy(false);onHeatmap(null);return()=>{generation.current++;frame.current?.remove();};},[layout,result]);
 async function check(){
  if(!result||disabled||busy)return;
  const run=++generation.current;setBusy(true);setError('');
  const iframe=document.createElement('iframe');frame.current=iframe;
  iframe.setAttribute('sandbox','allow-same-origin');iframe.setAttribute('aria-hidden','true');iframe.tabIndex=-1;iframe.inert=true;
  Object.assign(iframe.style,{position:'fixed',left:'-20000px',top:'0',width:layout.viewport.width+'px',height:layout.viewport.height+'px',border:'0'});
  try{
   const loaded=new Promise<void>((resolve,reject)=>{const timeout=setTimeout(()=>reject(new Error('Preview rendering timed out.')),15000);iframe.onload=()=>{clearTimeout(timeout);resolve();};});
   iframe.srcdoc=result.html.replace('<link rel="stylesheet" href="styles.css">',`<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none'"><style>${result.css}</style>`);
   document.body.appendChild(iframe);await loaded;
   const doc=iframe.contentDocument;if(!doc)throw new Error('Preview unavailable.');
   await doc.fonts.ready;
   await Promise.all(Array.from(doc.images).map(image=>image.decode()));
   const {toCanvas}=await import('html-to-image');
   const ratio=Math.min(1,960/Math.max(layout.viewport.width,layout.viewport.height));
   const width=Math.max(1,Math.round(layout.viewport.width*ratio)),height=Math.max(1,Math.round(layout.viewport.height*ratio));
   const rendered=await toCanvas(doc.body,{width:layout.viewport.width,height:layout.viewport.height,canvasWidth:width,canvasHeight:height,pixelRatio:1,skipFonts:true,backgroundColor:layout.background});
   if(run!==generation.current)return;
   const reference=await createImageBitmap(await(await fetch(source)).blob());
   const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
   const ctx=canvas.getContext('2d',{willReadFrequently:true})!,renderContext=rendered.getContext('2d',{willReadFrequently:true})!;
   try{ctx.fillStyle='#fff';ctx.fillRect(0,0,width,height);ctx.drawImage(reference,0,0,width,height);}finally{reference.close();}
   const a=ctx.getImageData(0,0,width,height).data,b=renderContext.getImageData(0,0,width,height).data;
   const heat=ctx.createImageData(width,height),cells=Array.from({length:16},()=>({total:0,count:0}));let changed=0;
   for(let i=0;i<a.length;i+=4){
    const d=(Math.abs(a[i]-b[i])+Math.abs(a[i+1]-b[i+1])+Math.abs(a[i+2]-b[i+2]))/3;
    const pixel=i/4,x=pixel%width,y=Math.floor(pixel/width),cell=Math.min(3,Math.floor(y*4/height))*4+Math.min(3,Math.floor(x*4/width));
    cells[cell].total+=d;cells[cell].count++;
    if(d>25){changed++;heat.data[i]=232;heat.data[i+1]=73;heat.data[i+2]=57;heat.data[i+3]=Math.round(Math.min(210,70+d));}
   }
   ctx.putImageData(heat,0,0);
   const issues:string[]=[];
   const outside=layout.elements.filter(e=>e.x+e.width>layout.viewport.width||e.y+e.height>layout.viewport.height).length;
   if(outside)issues.push(outside+' elements extend outside the canvas.');
   const clipped=Array.from(doc.querySelectorAll<HTMLElement>('main > [id]')).filter(e=>e.scrollWidth>e.clientWidth+2||e.scrollHeight>e.clientHeight+2).length;
   if(clipped)issues.push(clipped+' elements may have overflowing content.');
   const tiny=layout.elements.filter(e=>['text','button'].includes(e.type)&&(e.font_size??20)<12).length;
   if(tiny)issues.push(tiny+' text elements use a font smaller than 12 px.');
   const next={heatmap:canvas.toDataURL(),difference:Math.round(changed/(width*height)*1000)/10,issues,regions:cells.map((c,i)=>({x:i%4,y:Math.floor(i/4),score:c.total/Math.max(1,c.count)})).filter(c=>c.score>5).sort((a,b)=>b.score-a.score).slice(0,3)};
   if(run===generation.current){setReport(next);setShow(true);onHeatmap(next.heatmap);}
  }catch(e){if(run===generation.current)setError(e instanceof Error?e.message:'Visual check failed in this browser.');}
  finally{iframe.remove();if(frame.current===iframe)frame.current=null;if(run===generation.current)setBusy(false);}
 }
 return <details className="quality-panel"><summary>Quality checks</summary><p>Compare the rendered draft with your screenshot and flag layout issues.</p><button disabled={disabled||busy||!result} onClick={()=>void check()}>{busy?'Checking visual differences…':report?'Run check again':'Run quality check'}</button>{busy&&<p role="status">Rendering a local comparison…</p>}{error&&<p role="alert">{error}</p>}{report&&<div className="quality-report"><strong>{report.difference}% of sampled pixels differ</strong><p>Mean RGB difference above 25/255; sampled at up to 960 px. Fonts and antialiasing affect this result. This is not an accuracy score.</p><label><input type="checkbox" checked={show} onChange={e=>{setShow(e.target.checked);onHeatmap(e.target.checked?report.heatmap:null);}}/>Show red difference overlay</label>{report.issues.length?<ul>{report.issues.map(issue=><li key={issue}>{issue}</li>)}</ul>:<p>No overflow or small-font warnings found.</p>}{report.regions.length>0&&<p>Largest differences: {report.regions.map(r=>'row '+(r.y+1)+', column '+(r.x+1)).join('; ')} of a 4 × 4 grid.</p>}<small>Editing the draft clears this report. Run it again after changes.</small></div>}</details>;
}
