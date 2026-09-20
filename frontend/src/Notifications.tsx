import {useEffect, useState} from 'react';

type Notice = {id: string; message: string};
const eventName = 'screenweave:notice';

export function notify(message: string) {
  window.dispatchEvent(new CustomEvent<Notice>(eventName, {
    detail: {id: crypto.randomUUID(), message},
  }));
}

function Toast({notice, dismiss}: {notice: Notice; dismiss: (id: string) => void}) {
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    if (paused) return;
    const timer = window.setTimeout(() => dismiss(notice.id), 6000);
    return () => window.clearTimeout(timer);
  }, [notice.id, paused, dismiss]);
  return <div className="event-toast" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}
    onFocus={() => setPaused(true)} onBlur={event => {if (!event.currentTarget.contains(event.relatedTarget)) setPaused(false);}}>
    <span className="toast-symbol" aria-hidden="true">✓</span>
    <p role="status">{notice.message}</p>
    <button className="toast-close" aria-label="Dismiss notification" onClick={() => dismiss(notice.id)}>×</button>
  </div>;
}

export default function Notifications() {
  const [notices, setNotices] = useState<Notice[]>([]);
  // Stable callback keeps timers independent of newly arriving notifications.
  const [dismiss] = useState(() => (id: string) => setNotices(items => items.filter(item => item.id !== id)));
  useEffect(() => {
    const receive = (event: Event) => setNotices(items => [...items.slice(-2), (event as CustomEvent<Notice>).detail]);
    window.addEventListener(eventName, receive);
    return () => window.removeEventListener(eventName, receive);
  }, []);
  return <aside className="notification-stack" aria-label="Notifications">{notices.map(notice =>
    <Toast key={notice.id} notice={notice} dismiss={dismiss}/>
  )}</aside>;
}
