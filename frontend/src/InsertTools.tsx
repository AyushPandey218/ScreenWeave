import {useEffect, useRef, useState} from 'react';
import type {Element} from './ElementEditor';

export default function InsertTools({disabled, onAdd}: {disabled: boolean; onAdd: (type: string, image?: Partial<Element>) => void}) {
  const input = useRef<HTMLInputElement>(null);
  const current = useRef({disabled, onAdd});
  current.current = {disabled, onAdd};
  const alive = useRef(true);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  useEffect(() => {alive.current = true; return () => {alive.current = false;};}, []);
  async function insertImage(file?: File) {
    if (!file || busy || disabled) return;
    setError(''); setBusy(true);
    try {
      if (!['image/png', 'image/jpeg'].includes(file.type) || file.size > 5 * 1024 * 1024)
        throw new Error('Choose a PNG or JPEG under 5 MiB.');
      const bitmap = await createImageBitmap(file);
      try {
        if (bitmap.width * bitmap.height > 4000000) throw new Error('Choose an image under 4 megapixels.');
        const canvas = document.createElement('canvas');
        let size = Math.min(1, 512 / Math.max(bitmap.width, bitmap.height)), src = '';
        for (let attempt = 0; attempt < 10; attempt++) {
          canvas.width = Math.max(1, Math.round(bitmap.width * size));
          canvas.height = Math.max(1, Math.round(bitmap.height * size));
          const context = canvas.getContext('2d');
          if (!context) throw new Error('Your browser could not prepare this image.');
          context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
          src = canvas.toDataURL('image/png');
          if (src.length <= 200000) break;
          size *= .75;
        }
        if (src.length > 200000) throw new Error('This image is too detailed. Try a smaller image.');
        if (alive.current && !current.current.disabled)
          current.current.onAdd('image', {src, width: canvas.width, height: canvas.height});
      } finally {bitmap.close();}
    } catch (e) {
      if (alive.current) setError(e instanceof Error ? e.message : 'Could not add image.');
    } finally {if (alive.current) setBusy(false);}
  }
  return <div className="insert-tools">
    <div className="sidebar-heading"><strong>Add element</strong><span>＋</span></div>
    <div className="insert-grid">{[['text','T','Text'],['button','▣','Button'],['input','▭','Input'],['container','▢','Card']].map(([type,icon,label]) =>
      <button key={type} disabled={disabled} onClick={() => onAdd(type)} aria-label={'Add '+label.toLowerCase()}><span aria-hidden="true">{icon}</span>{label}</button>
    )}<button disabled={disabled || busy} onClick={() => input.current?.click()} aria-label="Add image"><span aria-hidden="true">▧</span>{busy ? 'Preparing…' : 'Image'}</button></div>
    <input ref={input} hidden type="file" accept="image/png,image/jpeg" aria-label="Image to insert" onChange={e => {void insertImage(e.target.files?.[0]);e.target.value='';}}/>
    {error && <p className="insert-error" role="alert">{error}</p>}
    <p className="insert-note">{disabled ? 'Maximum 500 elements reached.' : 'Images are resized to fit. Cards start behind other layers.'}</p>
  </div>;
}
