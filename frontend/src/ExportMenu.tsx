import {useEffect,useRef,useState} from 'react';
type Kind='html'|'react'|'tailwind';
export default function ExportMenu({disabled,tailwind,onDownload,onBackup}:{disabled:boolean;tailwind:boolean;onDownload:(kind:Kind)=>void;onBackup:()=>void}){
 const [open,setOpen]=useState(false),root=useRef<HTMLDivElement>(null),trigger=useRef<HTMLButtonElement>(null);
 useEffect(()=>{if(!open)return;function outside(e:PointerEvent){if(!root.current?.contains(e.target as Node))setOpen(false);}function escape(e:KeyboardEvent){if(e.key==='Escape'){setOpen(false);trigger.current?.focus();}}document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);};},[open]);
 return <div className="export-menu" ref={root}><button className="primary" ref={trigger} aria-expanded={open} aria-controls="export-options" onClick={()=>setOpen(!open)}>Export ↓</button>{open&&<div id="export-options" className="export-options" aria-label="Export options">
 <strong>Take your work with you</strong>
 {([['html','↓ HTML / CSS','Static website'],['react','↓ React project','React + TypeScript'],['tailwind','↓ React + Tailwind','React with utility classes']] as const).map(([kind,label,description])=><button key={kind} aria-label={label} disabled={disabled||(kind==='tailwind'&&!tailwind)} onClick={()=>{onDownload(kind);setOpen(false);trigger.current?.focus();}}>{label}<small>{description}</small></button>)}
 <button aria-label="↓ Project backup" onClick={()=>{onBackup();setOpen(false);trigger.current?.focus();}}>↓ Project backup<small>Reopen and edit in ScreenWeave</small></button>
 {disabled&&<p>Code downloads become available when the preview is up to date.</p>}
 </div>}</div>;
}
