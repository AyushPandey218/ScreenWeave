import assert from 'node:assert/strict';
import {mergeRegion} from './src/region.ts';
const element=(id,type,x,y,width,height,parent_id=null)=>({id,type,x,y,width,height,parent_id});
const base={version:1,viewport:{width:500,height:400},background:'#ffffff',limitations:[],elements:[
 element('outer','container',0,0,500,400),
 element('old','button',110,110,30,20,'outer'),
 element('crossing','text',90,120,40,20,'old'),
 element('outside','text',350,10,60,20)
]};
const region={x:100,y:100,width:100,height:100};
const patch={...base,viewport:{width:100,height:100},elements:[element('card','container',0,0,100,100),element('label','text',10,10,40,20,'card')]};
const merged=mergeRegion(base,region,patch);
assert.equal(merged.elements.length,5);
assert.deepEqual(merged.elements.find(e=>e.id==='outside'),base.elements[3]);
assert.equal(merged.elements.find(e=>e.id==='crossing').parent_id,null);
const newCard=merged.elements.find(e=>e.id.startsWith('region-')&&e.type==='container');
const newText=merged.elements.find(e=>e.id.startsWith('region-')&&e.type==='text');
assert.equal(newCard.parent_id,'outer');
assert.equal(newText.parent_id,newCard.id);
assert.equal(newText.x,110);assert.equal(newText.y,110);
assert.equal(base.elements[1].id,'old');
assert.throws(()=>mergeRegion(base,region,{...patch,elements:[]}));
assert.throws(()=>mergeRegion(base,{...region,x:490},patch));
assert.throws(()=>mergeRegion(base,region,{...patch,viewport:{width:101,height:100}}));
assert.throws(()=>mergeRegion(base,region,{...patch,elements:Array.from({length:500},(_,i)=>element('item'+i,'text',0,0,10,10))}));
console.log('Region merge preserves outside elements, remaps parents, offsets geometry, rejects empty/oversized/mismatched results.');
