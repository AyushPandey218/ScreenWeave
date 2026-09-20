import type { Layout } from './ElementEditor';
export type Project = { id: string; name: string; source: string; layout: Layout; original: Layout; updatedAt: number };
export type Result = { layout: Layout; html: string; css: string; exports: { html: string; react: string } };
async function transact<T>(mode: IDBTransactionMode, run: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await new Promise<IDBDatabase>((resolve,reject) => {
    const r = indexedDB.open('screenweave-projects',1);
    r.onupgradeneeded = () => r.result.createObjectStore('projects',{keyPath:'id'});
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(new Error('Browser storage unavailable.'));
  });
  return new Promise((resolve,reject) => {
    const tx=db.transaction('projects',mode); const r=run(tx.objectStore('projects'));
    tx.oncomplete=()=>{db.close();resolve(r.result);};
    tx.onerror=tx.onabort=()=>{db.close();reject(new Error('Could not save to browser storage. Check available space.'));};
  });
}
export const listProjects=()=>transact<Project[]>('readonly',s=>s.getAll());
export const getProject=(id:string)=>transact<Project|undefined>('readonly',s=>s.get(id));
export const saveProject=(p:Project)=>transact('readwrite',s=>s.put(p));
export const deleteProject=(id:string)=>transact('readwrite',s=>s.delete(id));
export function navigate(path:string){history.pushState({},'',path);window.dispatchEvent(new PopStateEvent('popstate'));}
const API=(import.meta.env.VITE_API_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
export async function apiRequest(path:string,body:BodyInit,type:string,signal?:AbortSignal):Promise<Result>{
  const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':type},body,signal});
  if(!r.ok){const e=await r.json().catch(()=>null);throw new Error(typeof e?.detail==='string'?e.detail:'Request failed. Please try again shortly.');}
  return r.json();
}

