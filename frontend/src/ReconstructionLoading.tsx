import {useEffect, useRef} from 'react';

type Props = {
  source: string;
  name: string;
  elapsed: number;
  saving: boolean;
  onCancel: () => void;
};

export default function ReconstructionLoading({source, name, elapsed, saving, onCancel}: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    element?.showModal();
    return () => {
      element?.close();
      document.body.style.overflow = previousOverflow;
    };
  }, []);
  const waiting = elapsed >= 25;
  const title = saving ? 'Your draft is ready.' : waiting ? 'Good things take a little processing.' : 'Weaving your interface.';
  const message = saving
    ? 'Saving your project in this browser before opening the editor.'
    : waiting
      ? 'We’re still waiting for the result. The service may need extra time to start after being idle.'
      : 'Turning the text, shapes, and details in your screenshot into an editable first draft.';
  return <dialog ref={dialog} className="reconstruction-dialog" aria-labelledby="reconstruction-title" aria-describedby="reconstruction-description" onCancel={event => {event.preventDefault(); if (!saving) onCancel();}}>
    <div className="loading-screen-header"><span className="brand"><img src="/favicon.svg" alt="" width="34" height="34"/>ScreenWeave</span><span className="loading-screen-label">YOUR NEXT INTERFACE IS TAKING SHAPE</span></div>
    <div className="loading-screen-center"><section className="reconstruction-loading">
    <div className="weave-preview" aria-hidden="true">
      <div className="weave-preview-top"><span/><span/><span/><small>YOUR REFERENCE</small></div>
      <div className="weave-preview-stage">
        <img src={source} alt=""/>
        <div className="weave-scan"/>
        <div className="weave-outline outline-one"/><div className="weave-outline outline-two"/>
        <span className="weave-tag">Screenshot → editable interface</span>
      </div>
      <div className="weave-preview-bottom"><span className="spinner"/><span>{saving ? 'Draft received' : 'Reconstruction in progress'}</span></div>
    </div>
    <div className="weave-content">
      <span className="weave-badge"><img src="/favicon.svg" alt="" width="20" height="20"/> SCREENWEAVE STUDIO</span>
      <div role="status" aria-live="polite" aria-atomic="true">
        <h2 id="reconstruction-title">{title}</h2>
        <p id="reconstruction-description" className="weave-description">{message}</p>
      </div>
      <ol className="weave-steps" aria-label="Reconstruction progress">
        <li className="complete"><span>✓</span><div><strong>Reference selected</strong><small title={name}>{name}</small></div></li>
        <li className={saving ? 'complete' : 'current'} aria-current={!saving ? 'step' : undefined}><span>{saving ? '✓' : <i className="spinner"/>}</span><div><strong>Create editable draft</strong><small>Text, controls, and layout</small></div></li>
        <li className={saving ? 'current' : ''} aria-current={saving ? 'step' : undefined}><span>{saving ? <i className="spinner"/> : '3'}</span><div><strong>Open your workspace</strong><small>Save locally, then start editing</small></div></li>
      </ol>
      <div className="weave-tip"><span aria-hidden="true">✦</span><p><strong>Make it yours next.</strong> You’ll be able to move elements, adjust corners and colors, and export your draft as React or HTML.</p></div>
      <div className="weave-loading-footer">
        <span className="weave-elapsed" aria-live="off">{Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')} elapsed</span>
        <button autoFocus onClick={onCancel} disabled={saving}>Cancel reconstruction</button>
      </div>
      <p className="weave-footnote">Keep this page open. Your editor opens automatically when the draft is saved.</p>
    </div>
  </section></div>
  </dialog>;
}
