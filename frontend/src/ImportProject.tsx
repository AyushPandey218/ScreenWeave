import {useRef, useState} from 'react';
import {parseProjectBackup} from './projectBackup';
import {saveProject} from './projects';
import {notify} from './Notifications';

export default function ImportProject({onImported}: {onImported: () => void}) {
  const input = useRef<HTMLInputElement>(null);
  const [busy,setBusy] = useState(false), [error,setError] = useState('');
  async function restore(file?: File) {
    if (!file || busy) return;
    setBusy(true);setError('');
    try {
      if (file.size > 25 * 1024 * 1024) throw new Error('Choose a backup under 25 MiB.');
      const project = parseProjectBackup(await file.text());
      const image = await createImageBitmap(await (await fetch(project.source)).blob());
      try {
        if (image.width !== project.layout.viewport.width || image.height !== project.layout.viewport.height)
          throw new Error('Reference image dimensions do not match the project.');
      } finally {image.close();}
      await saveProject({...project, id:crypto.randomUUID(), updatedAt:Date.now()});
      onImported();notify('Project imported as a new copy.');
    } catch (e) {setError(e instanceof Error ? e.message : 'Could not import this backup.');}
    finally {setBusy(false);}
  }
  return <div className="import-project">
    <button disabled={busy} onClick={() => input.current?.click()}>{busy ? 'Importing…' : '↑ Import project'}</button>
    <input ref={input} hidden type="file" accept=".json,.screenweave" aria-label="Project backup to import" onChange={e => {void restore(e.target.files?.[0]);e.target.value='';}}/>
    {error && <p className="import-error" role="alert">{error}</p>}
  </div>;
}
