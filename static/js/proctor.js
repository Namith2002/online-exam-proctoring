// static/js/proctor.js
// expects global variables:
// ATTEMPT_ID, IMG_UPLOAD, SAVE_ANSWER_URL, LOG_EVENT_URL, SERVER_ALLOWED_UNTIL (optional ISO string)

(function(){
  const video = document.getElementById('video');
  const proctorStatus = document.getElementById('proctorStatus');
  const consentAccept = document.getElementById('consentAccept');
  const consentReject = document.getElementById('consentReject');
  const consentModal = document.getElementById('consentModal');

  let stream = null;
  let snapshotInterval = null;

  function setStatus(msg, type) {
    if (!proctorStatus) return;
    proctorStatus.textContent = msg;
    proctorStatus.classList.remove('status-badge', 'success', 'warning', 'danger');
    proctorStatus.classList.add('status-badge');
    if (type) proctorStatus.classList.add(type);
  }

  async function startMedia() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      video.srcObject = stream;
      try { await video.play(); } catch(_) {}
      setStatus("Webcam active for proctoring (consent given)", 'success');
      initSnapshotInterval();
    } catch (err) {
      console.error(err);
      setStatus("Unable to access camera: " + err.message, 'danger');
      const retryId = 'proctor-retry';
      let btn = document.getElementById(retryId);
      if (!btn) {
        btn = document.createElement('button');
        btn.id = retryId;
        btn.className = 'btn small warning';
        btn.textContent = 'Retry Permissions';
        btn.addEventListener('click', startMedia);
        if (proctorStatus) proctorStatus.appendChild(btn);
      }
    }
  }

  // consent handlers
  if (consentAccept) {
    consentAccept.addEventListener('click', () => {
      consentModal.style.display = 'none';
      startMedia();
      startClientTimer();
    });
  }
  if (consentReject) {
    consentReject.addEventListener('click', () => {
      window.location.href = "/";
    });
  }

  // capture frame, resize and compress to JPEG, then upload
  function captureAndUpload() {
    if (!video || !video.videoWidth) return;
    const MAX_WIDTH = 640; // reduce if you want smaller files
    let w = video.videoWidth;
    let h = video.videoHeight;
    if (w > MAX_WIDTH) {
      const ratio = MAX_WIDTH / w;
      w = Math.round(w * ratio);
      h = Math.round(h * ratio);
    }
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, w, h);
    // compress to JPEG at quality 0.6
    const dataUrl = canvas.toDataURL('image/jpeg', 0.6);
    const fd = new FormData();
    fd.append('attempt_id', ATTEMPT_ID);
    fd.append('image', dataUrl);
    fetch(IMG_UPLOAD, { method: 'POST', body: fd, credentials: 'same-origin' })
      .then(res => {
        if (!res.ok) {
          console.warn("Image upload returned", res.status, res.statusText);
        }
      })
      .catch(e => console.error("img upload failed", e));
  }

  function initSnapshotInterval() {
    captureAndUpload();
    snapshotInterval = setInterval(captureAndUpload, 15000);
  }

  // autosave answers
  document.querySelectorAll('.question input[type=radio]').forEach(radio => {
    radio.addEventListener('change', async (e) => {
      const qDiv = e.target.closest('.question');
      const questionId = qDiv.dataset.qid;
      const selected = e.target.value;
      try {
        await fetch(SAVE_ANSWER_URL, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ attempt_id: ATTEMPT_ID, question_id: questionId, selected: selected })
        });
      } catch (err) { console.error("save answer failed", err); }
    });
  });

  // log events
  async function logEvent(ev, detail="") {
    const payload = { attempt_id: ATTEMPT_ID, event: ev, detail: detail };
    try {
      const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
      navigator.sendBeacon(LOG_EVENT_URL, blob);
    } catch (e) {
      fetch(LOG_EVENT_URL, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) }).catch(()=>{});
    }
  }

  document.addEventListener('visibilitychange', () => {
    const ev = document.visibilityState === 'visible' ? 'tab_visible' : 'tab_hidden';
    logEvent(ev, document.visibilityState);
  });
  window.addEventListener('blur', () => logEvent('window_blur', ''));
  window.addEventListener('focus', () => logEvent('window_focus', ''));

  // client-side timer using SERVER_ALLOWED_UNTIL when available
  let clientTimerInterval = null;
  function startClientTimer() {
    const timerEl = document.getElementById('timer');
    if (!timerEl) return;
    let allowedUntil = null;
    if (typeof SERVER_ALLOWED_UNTIL !== 'undefined' && SERVER_ALLOWED_UNTIL) {
      try {
        allowedUntil = new Date(SERVER_ALLOWED_UNTIL);
      } catch (e) {
        allowedUntil = null;
      }
    }
    if (!allowedUntil) {
      const minutes = parseInt(document.getElementById('examDuration').dataset.minutes || "60");
      allowedUntil = new Date(Date.now() + minutes * 60 * 1000);
    }
    function updateTimer() {
      const now = new Date();
      const diff = allowedUntil - now;
      if (diff <= 0) {
        timerEl.textContent = "00:00";
        clearInterval(clientTimerInterval);
        // auto-submit form
        const submitBtn = document.querySelector('#examForm button[type=submit]');
        if (submitBtn) submitBtn.click();
        return;
      }
      const mm = String(Math.floor(diff / 60000)).padStart(2, '0');
      const ss = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0');
      timerEl.textContent = `${mm}:${ss}`;
      if (diff < 60000) { timerEl.classList.add('danger'); } else { timerEl.classList.remove('danger'); }
    }
    updateTimer();
    clientTimerInterval = setInterval(updateTimer, 1000);
  }

  window.addEventListener('beforeunload', (e) => {
    try {
      captureAndUpload();
      logEvent('beforeunload', '');
      if (stream) {
        try { stream.getTracks().forEach(t => t.stop()); } catch(_) {}
      }
    } catch (err) {}
  });

  // Stop proctoring before actual form submission to avoid concurrent writes
  const examForm = document.getElementById('examForm');
  if (examForm) {
    examForm.addEventListener('submit', () => {
      try {
        if (snapshotInterval) {
          clearInterval(snapshotInterval);
          snapshotInterval = null;
        }
        if (stream) {
          try { stream.getTracks().forEach(t => t.stop()); } catch(_) {}
        }
        setStatus('Proctoring stopped, submitting exam...', 'success');
      } catch (_) {}
    });
  }

  if (!consentModal) {
    startMedia();
    startClientTimer();
  }
})();
