"""Export named, typed React primitives shared by all reconstructed instances."""
import json
from .responsive import groups, responsive_css


def componentize(layout,files,tailwind):
    declarations='''import type {MouseEventHandler} from 'react';
export type ReconstructedElementData = {id:string;type:string;text?:string;src?:string};
export type ElementProps = {element:ReconstructedElementData;className?:string};
export function ReconstructedButton({element,className,onClick}:ElementProps & {onClick?:MouseEventHandler<HTMLButtonElement>}) {return <button id={element.id} className={className} type="button" onClick={onClick}>{element.text??''}</button>;}
export function ReconstructedInput({element,className}:ElementProps) {return <input id={element.id} className={className} aria-label={element.text||'Reconstructed input'} autoComplete="off"/>;}
export function ReconstructedText({element,className}:ElementProps) {return <div id={element.id} className={className}>{element.text??''}</div>;}
export function ReconstructedImage({element,className}:ElementProps) {return <img id={element.id} className={className} src={element.src} alt={element.text||'Reconstructed graphic'}/>;}
export function ReconstructedCard({element,className}:ElementProps) {return <div id={element.id} className={className} aria-hidden="true"/>;}
export function ReconstructedElement(props:ElementProps) {switch(props.element.type){case 'button':return <ReconstructedButton {...props}/>;case 'input':return <ReconstructedInput {...props}/>;case 'text':return <ReconstructedText {...props}/>;case 'image':return <ReconstructedImage {...props}/>;default:return <ReconstructedCard {...props}/>;}}
'''
    files['src/components.tsx']=declarations
    imports='import layout from "./layout.json";\nimport {ReconstructedElement} from "./components";\n'
    if tailwind:
        imports+='import {elementClasses,pageClasses} from "./classes";\n'
    render='<ReconstructedElement key={element.id} element={element}'+(' className={elementClasses[element.id]}' if tailwind else '')+'/>'
    page='"page "+pageClasses' if tailwind else '"page"'
    if layout.get('responsive'):
        imports+='const groups: string[][] = '+json.dumps([g['ids'] for g in groups(layout)])+';\n'
        body='{groups.map((ids,i)=><section className="responsive-group" data-group={i} key={i}>{ids.map(id=>{const element=layout.elements.find(e=>e.id===id)!;return '+render+';})}</section>)}'
    else:
        body='{layout.elements.map(element=>'+render+')}'
    files['src/App.tsx']=imports+'export default function App(){return <main className={'+page+'}>'+body+'</main>;}\n'
    if tailwind:
        files['src/styles.css']+='\n'+responsive_css(layout)
    if layout.get('responsive'):
        files['README.md']=files['README.md'].replace('This is a static reconstruction at the original viewport size.', 'This export preserves desktop geometry and stacks inferred groups below 640 px.').replace('this export does not infer responsive behavior or add', 'mobile stacking is optional and this export does not add')
    files['README.md']+='\n## Reusable components\nNamed typed Button, Input, Text, Image and Card primitives live in src/components.tsx. ReconstructedButton accepts onClick. These are reusable primitives, not inferred business logic or automatically discovered composite card templates.\n\n'+('Mobile stacking is enabled at 640px. Groups are inferred from parent relationships; internal contents scale proportionally. Review small text and grouping before production. Edit src/styles.css to refine the layout.\n' if layout.get('responsive') else 'The layout preserves the source viewport. Enable mobile stacking in ScreenWeave to export narrow-screen group stacking.\n')
