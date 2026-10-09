/* Phone video pause / play button (css/phone-video.css). Respects reduced motion: those visitors
   start paused on the first frame and can press play. */
(() => {
  const PAUSE = '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12"/><rect x="9.5" y="2" width="3.5" height="12"/></svg>';
  const PLAY = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2v12l10-6z"/></svg>';
  document.querySelectorAll('.pv-demo').forEach((fig) => {
    const video = fig.querySelector('video'), btn = fig.querySelector('.pv-toggle');
    if (!video || !btn) return;
    const sync = () => {
      const playing = !video.paused;
      btn.innerHTML = playing ? PAUSE : PLAY;
      btn.setAttribute('aria-label', playing ? 'Pause the video' : 'Play the video');
    };
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { video.removeAttribute('autoplay'); video.pause(); }
    btn.addEventListener('click', () => { video.paused ? video.play() : video.pause(); });
    video.addEventListener('play', sync); video.addEventListener('pause', sync);
    sync();
  });
})();
