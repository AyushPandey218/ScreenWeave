import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { ElementEditor, type Element, type Layout } from './ElementEditor';

type Result = {
  layout: Layout;
  html: string; css: string; exports: { html: string; react: string };
};
const API = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [source, setSource] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [draft, setDraft] = useState<Layout | null>(null);
  const [selected, setSelected] = useState('');
  const [updating, setUpdating] = useState(false);
  const [editError, setEditError] = useState('');
  const revision = useRef(0);
  const [editRevision, setEditRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'preview' | 'html' | 'css'>('preview');
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const preview = useRef<HTMLDivElement>(null);
  const [previewWidth, setPreviewWidth] = useState(500);
  const [previewHeight, setPreviewHeight] = useState(326);

  useEffect(() => {
    if (!draft || !editRevision) return;
    const controller = new AbortController();
    const current = revision.current;
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`${API}/render`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(draft), signal: controller.signal });
        if (!response.ok) throw new Error('Could not apply edits. Check the backend and try another change.');
        const next = await response.json();
        if (current === revision.current && !controller.signal.aborted) { setResult(next); setUpdating(false); setEditError(''); }
      } catch (reason) {
        if (!controller.signal.aborted && current === revision.current) { setUpdating(false); setEditError(reason instanceof Error ? reason.message : 'Edits could not be applied.'); }
      }
    }, 300);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [draft, editRevision]);

  function changeElement(patch: Partial<Element>) {
    revision.current += 1;
    setUpdating(true); setEditError('');
    setDraft(previous => previous ? { ...previous, elements: previous.elements.map(e => e.id === selected ? { ...e, ...patch } : e) } : previous);
    setEditRevision(n => n + 1);
  }
  function clearEdits() {
    revision.current += 1; setDraft(null); setSelected(''); setEditRevision(0); setUpdating(false); setEditError('');
  }

  useEffect(() => {
    if (!file) { setSource(''); return; }
    const url = URL.createObjectURL(file); setSource(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => {
    if (!preview.current) return;
    const observer = new ResizeObserver(([entry]) => { setPreviewWidth(entry.contentRect.width); setPreviewHeight(entry.contentRect.height); });
    observer.observe(preview.current); return () => observer.disconnect();
  }, [tab, result]);

  function select(candidate?: File) {
    if (!candidate || busy) return;
    clearEdits(); setResult(null); setError(''); setFile(null);
    if (!['image/png', 'image/jpeg'].includes(candidate.type)) { setError('Choose a PNG or JPEG screenshot.'); return; }
    if (candidate.size > 5 * 1024 * 1024) { setError('Your screenshot must be smaller than 5 MiB.'); return; }
    setFile(candidate); setTab('preview');
  }

  async function generate() {
    if (!file || busy) return;
    clearEdits(); setBusy(true); setError(''); setResult(null);
    try {
      const response = await fetch(`${API}/reconstruct`, { method: 'POST', headers: { 'Content-Type': file.type }, body: file, signal: AbortSignal.timeout(120000) });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(typeof body?.detail === 'string' ? body.detail : `Processing failed (${response.status}). Please try again.`);
      }
      const next: Result = await response.json(); setResult(next); setDraft(next.layout); setSelected(next.layout.elements[0]?.id ?? ''); setTab('preview');
    } catch (reason) {
      setError(reason instanceof Error && reason.name === 'TimeoutError' ? 'The request timed out. The backend may be starting up; try again shortly.' : reason instanceof TypeError ? 'Cannot reach the backend. Check that the service is running and allows this frontend address.' : reason instanceof Error ? reason.message : 'Something went wrong. Please try again.');
    } finally { setBusy(false); }
  }

  function download(kind: 'html' | 'react') {
    if (!result || updating || editError) return;
    const bytes = Uint8Array.from(atob(result.exports[kind]), c => c.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], { type: 'application/zip' }));
    const link = document.createElement('a'); link.href = url; link.download = `screenweave-${kind}.zip`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const scale = result ? Math.min(1, previewWidth / result.layout.viewport.width, previewHeight / result.layout.viewport.height) : 1;
  const srcDoc = result?.html.replace('<link rel="stylesheet" href="styles.css">', `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none'"><style>${result.css}</style>`);

  return <>
    <header><a className="brand" href="/" aria-label="ScreenWeave home"><span className="mark">▧</span> ScreenWeave</a><span className="badge">EXPERIMENTAL BUILD</span></header>
    <main className="workspace">
      <div className="intro"><div><p className="eyebrow">FROM REFERENCE TO REAL CODE</p><h1>A screenshot.<br /><span>A starting point.</span></h1><p className="subtitle">Reconstruct an interface, inspect the result, and take the code with you.</p></div><div className="step-note"><strong>01 / RECONSTRUCT</strong><span>Start with a simple login or landing page.</span></div></div>
      <div className="toolbar"><div className="project-title">Untitled interface <span>{file ? file.name : 'No screenshot selected'}</span></div><div className="export-actions"><button disabled={!result || busy || updating || !!editError} onClick={() => download('html')}>↓ HTML / CSS</button><button disabled={!result || busy || updating || !!editError} onClick={() => download('react')}>↓ React project</button></div></div>
      <div className="panels">
        <section className="panel"><div className="panel-heading"><h2><span>01</span> Original screenshot</h2><button className="text-button" disabled={busy} onClick={() => input.current?.click()}>{file ? 'Replace' : 'Browse'}</button></div>
          <input ref={input} type="file" accept="image/png,image/jpeg" hidden onChange={e => { select(e.target.files?.[0]); e.target.value = ''; }} />
          <div className={`source-area ${drag ? 'dragging' : ''}`} onDragOver={e => { e.preventDefault(); if (!busy) setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={e => { e.preventDefault(); setDrag(false); select(e.dataTransfer.files[0]); }}>
            {source ? <img className="source-image" src={source} alt="Uploaded screenshot" /> : <button className="upload" onClick={() => input.current?.click()}><span className="upload-icon">↥</span><strong>Drop your screenshot here</strong><span>or click to browse files</span><small>PNG or JPG · up to 5 MiB · 4 megapixels</small></button>}
          </div>
          <div className="source-footer"><span>{file ? `${(file.size / 1024).toFixed(0)} KB · Ready to reconstruct` : 'Your reference stays yours. Uploads are not saved.'}</span><button className="primary" disabled={!file || busy} onClick={generate}>{busy ? 'Reconstructing…' : 'Reconstruct →'}</button></div>
        </section>
        <section className="panel"><div className="panel-heading"><h2><span>02</span> Reconstruction</h2><div className="tabs" aria-label="Output view">{(['preview', 'html', 'css'] as const).map(t => <button key={t} aria-pressed={tab === t} onClick={() => setTab(t)}>{t === 'preview' ? 'Preview' : t.toUpperCase()}</button>)}</div></div>
          {result ? tab === 'preview' ? <div className="preview-area" ref={preview}><div className="preview-stage" style={{ height: result.layout.viewport.height * scale, width: result.layout.viewport.width * scale }}><iframe title="Reconstructed website" sandbox="" srcDoc={srcDoc} style={{ width: result.layout.viewport.width, height: result.layout.viewport.height, transform: `scale(${scale})`, transformOrigin: 'top left' }} />{result.layout.elements.map(e => <button key={e.id} className={`element-hit ${selected === e.id ? 'selected' : ''}`} aria-label={`Select ${e.type} ${e.text || e.id}`} title={`${e.type}: ${e.text || e.id}`} onClick={() => setSelected(e.id)} style={{ left: e.x * scale, top: e.y * scale, width: e.width * scale, height: e.height * scale }} />)}</div></div> : <pre className="code"><code>{tab === 'html' ? result.html : result.css}</code></pre> : <div className="empty-output" aria-live="polite"><div className={busy ? 'placeholder-grid working' : 'placeholder-grid'}><i /><i /><i /></div><strong>{busy ? 'Finding text and interface elements' : 'Your next interface starts here'}</strong><p>{busy ? 'The first request may take longer while the service starts.' : 'Upload a reference to generate a live preview and exportable code.'}</p></div>}
          <div className="result-footer"><span className={result ? 'status-dot ready' : 'status-dot'} />{result ? `${result.layout.elements.length} elements · ${result.layout.viewport.width} × ${result.layout.viewport.height} · Fixed viewport` : busy ? 'Processing your screenshot' : 'Waiting for a screenshot'}</div>
        </section>
      </div>
      {draft && <ElementEditor layout={draft} selected={selected} onSelect={setSelected} onChange={changeElement} status={updating ? 'Applying changes…' : editError ? 'Changes not applied' : 'Preview and exports up to date'} />}
      {editError && <div className="error" role="alert">{editError}<button onClick={() => { setUpdating(true); setEditError(''); setEditRevision(n => n + 1); }}>Retry edits</button></div>}
      {error && <div className="error" role="alert">{error}</div>}
      <footer className="notes"><span>Built for a first draft. Refined by you.</span><p>Select an element to refine its properties. Edits update both exports. Exports contain static UI, without application logic. Changes last for this session.</p></footer>
    </main>
  </>;
}
createRoot(document.getElementById('root')!).render(<App />);
