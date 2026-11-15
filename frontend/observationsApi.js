/* =========================================================================
 * observationsApi.js — adaptateur entre le frontend SPHEREx et notre backend
 * -------------------------------------------------------------------------
 * Le frontend (main.js) appelle :
 *     window.ObservationsApi.fetchObservations({ ra, dec, fov, band, target })
 * et attend en retour :
 *     { frames: [ { date, band, imageUrl, fov, ... }, ... ] }
 *
 * Ce fichier appelle GET /api/motion du backend et convertit la réponse.
 * Chaque "frame" correspond à UNE image de la vidéo (même ordre que la vidéo).
 * Champs en plus (ignorés par main.js tant qu'on ne les utilise pas) :
 *     videoTime  : instant (s) de cette image dans la vidéo MP4 -> video.currentTime
 *     group, groupChanged, previousGroup, disagreement, note, status, snr ...
 * La réponse contient aussi :
 *     video    : { mp4, mp4Markers, durationS, width, height }  (URLs absolues)
 *     motion   : mouvement mesuré (µ, incertitudes, statut)
 *     raw      : réponse complète du backend
 *
 * Adresse du backend :
 *   - page servie par le backend (http://localhost:8000/app/) -> même adresse, rien à régler
 *   - page ouverte autrement (fichier, Live Server...)        -> http://localhost:8000
 *   - backend sur un autre PC : définir AVANT ce script
 *       <script>window.SPHEREX_API_BASE = "http://192.168.1.20:8000";</script>
 * ========================================================================= */
(function () {
  "use strict";

  const SERVED_BY_BACKEND =
    /^https?:$/.test(location.protocol) && location.pathname.startsWith("/app");
  const API_BASE = (
    window.SPHEREX_API_BASE || (SERVED_BY_BACKEND ? location.origin : "http://localhost:8000")
  ).replace(/\/+$/, "");
  const MAX_FOV_ARCMIN = 12;          // limite du backend (size_arcmin entre 1 et 12)
  const DEMO_SIZE_ARCMIN = 6;         // taille précalculée par run_all (défaut du backend)
  // 1er calcul d'une cible : de quelques minutes à plus d'une demi-heure (téléchargements IRSA).
  // On attend jusqu'à 1 h ; le serveur continue de toute façon et met le résultat en cache.
  const TIMEOUT_MS = 60 * 60 * 1000;
  // Cibles démo connues du backend (position corrigée du mouvement propre)
  const KNOWN_TARGETS = [
    [/barnard/i, "barnard"],
    [/wise\s*j?0855/i, "wise 0855-0714"],
    [/eps(ilon)?\s*ind/i, "eps indi b"],
  ];

  // "Band 3 (1.64–2.42 µm)" -> "D3" ; "All 102 Ch ..." -> null (tous les détecteurs)
  function bandToDetector(band) {
    const m = /Band\s*([1-6])/i.exec(band || "");
    return m ? `D${m[1]}` : null;
  }

  // "/files/..." -> "http://localhost:8000/files/..."
  function absUrl(u) {
    if (!u) return null;
    return /^https?:\/\//i.test(u) ? u : API_BASE + (u.startsWith("/") ? u : "/" + u);
  }

  function formatDate(iso) {
    // "2025-08-30T12:34:56..." -> "2025-08-30 12:34 UTC"
    if (!iso) return "";
    const s = String(iso).replace("T", " ");
    return s.length >= 16 ? s.slice(0, 16) + " UTC" : s;
  }

  function formatBand(e) {
    const parts = [];
    if (e.detector) parts.push(e.detector);
    if (typeof e.wavelength_um === "number") parts.push(`${e.wavelength_um.toFixed(3)} µm`);
    // (les désaccords / changements de groupe sont affichés à droite, pas sous la vidéo)
    return parts.join(" · ");
  }

  // ---- requêtes en cours (une seule par URL) et compteur de progression unique
  const pending = new Map();   // url -> { t0, promise }
  let progressTimer = null;
  let progressUrl = null;

  function stopProgress() {
    clearInterval(progressTimer);
    progressTimer = null;
    progressUrl = null;
  }

  // Un seul compteur à la fois : celui de la cible affichée (sinon plusieurs
  // compteurs écrivent dans la même case et le temps « saute »).
  function fmtElapsed(s) {
    const m = Math.floor(s / 60);
    return m ? `${m} min ${String(s % 60).padStart(2, "0")} s` : `${s} s`;
  }

  function showProgress(label, t0, url) {
    stopProgress();
    progressUrl = url;
    const statusEl = document.getElementById("timeline-status");
    const tick = () => {
      if (!statusEl || !statusEl.classList.contains("loading")) return;
      const s = Math.round((Date.now() - t0) / 1000);
      statusEl.textContent =
        `Calcul SPHEREx en cours pour ${label}… ${fmtElapsed(s)} ` +
        `(premier calcul : téléchargement des images depuis IRSA, plusieurs minutes ; ` +
        `ensuite c'est instantané). Vous pouvez laisser la page ouverte.`;
    };
    tick();
    progressTimer = setInterval(tick, 1000);
  }

  async function requestMotion(url) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
    let res;
    try {
      res = await fetch(url, { signal: ctrl.signal, cache: "no-store" });   // toujours la dernière version
    } catch (err) {
      if (err.name === "AbortError") {
        throw new Error("Le calcul continue sur le serveur. Recliquez sur la cible dans quelques " +
                        "minutes : le résultat s'affichera dès qu'il sera prêt.");
      }
      throw new Error(`Backend injoignable (${API_BASE}). Le serveur est-il lancé ?`);
    } finally {
      clearTimeout(timer);
    }
    if (!res.ok) {
      let detail = "";
      try { detail = JSON.stringify((await res.json()).detail); } catch (_) {}
      console.warn("Réponse du backend", res.status, detail);   // détail technique : console
      if (res.status === 502 || res.status === 503 || res.status === 504 ||
          /IRSA|Proxy Error|Server Error/i.test(detail)) {
        throw new Error("Le service de la NASA qui fournit les images SPHEREx (IRSA) ne répond pas " +
                        "en ce moment. Ce n'est pas un problème du site : réessayez dans quelques " +
                        "minutes. Les cibles déjà calculées restent disponibles.");
      }
      if (res.status === 422) {
        throw new Error("Coordonnées ou paramètres refusés par le serveur : vérifiez RA (0 à 360) " +
                        "et Dec (-90 à +90).");
      }
      throw new Error(`Le serveur a rencontré une erreur (${res.status}). Réessayez ; si elle ` +
                      "revient, regardez la fenêtre du serveur.");
    }
    return res.json();
  }

  // Position (pixels de grille) -> pixels de la vidéo propre (nord en haut, coins rognés)
  function toVideoPx(p, video) {
    if (!p || !video?.px_scale || !video?.grid_size_px) return null;
    const s = video.px_scale, c = video.crop_px || 0;
    return { x: (p[0] + 0.5) * s - c, y: video.grid_size_px * s - c - (p[1] + 0.5) * s };
  }

  async function fetchObservations({ ra, dec, fov, band, target } = {}) {
    if (ra === undefined || dec === undefined || ra === null || dec === null) {
      throw new Error("Coordonnées RA/Dec manquantes.");
    }
    // Cibles du catalogue : taille précalculée (réponse instantanée depuis le cache).
    // Autre taille = nouveau téléchargement de toutes les découpes IRSA (plus de 10 min).
    // Toutes les cibles du catalogue du front utilisent la taille précalculée
    // (scripts/precompute_front.py) ; seule une position saisie à la main suit le FOV.
    const isCatalog = !!(target?.id && target.id !== "custom-field");
    const size = isCatalog
      ? DEMO_SIZE_ARCMIN
      : Math.min(MAX_FOV_ARCMIN, Math.max(1, Number(fov) || DEMO_SIZE_ARCMIN));
    // Étoiles à fort mouvement propre : envoyer le NOM, le backend recentre
    // la position à l'époque SPHEREx (des coordonnées J2000 seraient décalées de plusieurs ').
    const tName = String(target?.name || "");
    const backendName =
      target?.backendName || (KNOWN_TARGETS.find(([re]) => re.test(tName)) || [])[1];
    const params = backendName
      ? new URLSearchParams({ name: backendName, size_arcmin: String(size) })
      : new URLSearchParams({ ra: String(ra), dec: String(dec), size_arcmin: String(size) });
    const detector = bandToDetector(band);
    if (detector) params.set("detector", detector);

    // Pas d'image de la cible précédente pendant le calcul
    const img = document.getElementById("cutout-img");
    if (img) img.removeAttribute("src");

    const url = `${API_BASE}/api/motion?${params}`;
    const label = target?.shortName || target?.name || `RA ${ra}, Dec ${dec}`;
    // Même requête déjà en cours (on a quitté la cible puis on y revient) :
    // on la réutilise au lieu d'en lancer une 2e, et le compteur continue où il en était.
    let job = pending.get(url);
    if (!job) {
      job = { t0: Date.now(), promise: requestMotion(url) };
      pending.set(url, job);
      job.promise.finally(() => pending.delete(url)).catch(() => {});
    }
    showProgress(label, job.t0, url);
    let data;
    try {
      data = await job.promise;
    } finally {
      if (progressUrl === url) stopProgress();
    }
    const fovLabel = `${size} arcmin`;
    const allView = toView(data?.display?.sequences?.[0], fovLabel, {
      id: "all",
      title: "Tous les groupes (trajectoire complète)",
    });
    // une vue par groupe (même détecteur, λ à ±3 %), choisie par l'utilisateur
    // seulement les groupes qui ont une vraie vidéo (au moins 2 images)
    const groupViews = (data?.display?.group_sequences || [])
      .map((sq) => toView(sq, fovLabel, { id: sq.groups?.[0], title: sq.title, info: sq.info }))
      .filter((v) => v.frames.length >= 2);
    const views = [allView, ...groupViews].filter((v) => v.frames.length);

    return {
      frames: allView.frames,
      video: allView.video,
      views,
      alert: data?.display?.alert || null,   // message court sur l'accord entre groupes
      targetLabel: data?.target_label || target?.name || "",
      summary: data?.display?.summary || "",
      motion: data?.motion || null,
      // fraîcheur des données (mise à jour automatique hebdomadaire côté serveur)
      update: data?.update || null,
      resultKey: data?.result_key || null,
      raw: data,
    };
  }

  /* État des mises à jour automatiques (nouvelles images SPHEREx publiées sur IRSA). */
  async function fetchUpdateStatus() {
    const res = await fetch(`${API_BASE}/api/updates/status`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  // Une séquence du backend (vidéo + frise) -> { id, title, info, frames, video }
  function toView(seq, fovLabel, meta) {
    const video = seq?.video;
    const timeline = video?.timeline || [];
    const frames = timeline.map((e) => ({
      date: formatDate(e.date_utc),
      band: formatBand(e),
      imageUrl: absUrl(e.image_url),
      fov: fovLabel,
      // --- extras pour la synchronisation vidéo / la case de détails ---
      videoTime: e.seek_s,
      // repère de la cible dans la vidéo (pixels vidéo) : mesuré, sinon prédit
      markerMeasured: toVideoPx(e.target_measured_px, video),
      markerPredicted: toVideoPx(e.target_predicted_px, video),
      usedInFit: e.used_in_fit !== false,
      tStart: e.t_start_s,
      tEnd: e.t_end_s,
      dateUtc: e.date_utc,
      detector: e.detector,
      wavelengthUm: e.wavelength_um,
      group: e.group,
      groupChanged: !!e.group_changed,
      previousGroup: e.previous_group,
      disagreement: !!e.disagreement,
      segmentLabel: e.segment_label,
      note: e.note,
      status: e.status,
      snr: e.snr,
    }));
    return {
      ...meta,
      frames,
      video: video
        ? {
            mp4: absUrl(video.mp4),
            mp4Markers: absUrl(video.mp4_markers),
            durationS: video.duration_s,
            pxScale: video.px_scale,
            cropPx: video.crop_px || 0,
            width: video.width,
            height: video.height,
          }
        : null,
    };
  }

  /* Synchronisation optionnelle avec une balise <video> :
   *   ObservationsApi.indexAtTime(frames, video.currentTime) -> indice de l'image affichée
   *   video.currentTime = frames[i].videoTime                 -> aller à une date
   */
  function indexAtTime(frames, t) {
    let idx = 0;
    for (let i = 0; i < frames.length; i++) {
      if (typeof frames[i].tStart === "number" && t >= frames[i].tStart - 1e-3) idx = i;
    }
    return idx;
  }

  window.ObservationsApi = { fetchObservations, fetchUpdateStatus, indexAtTime, API_BASE };
})();
