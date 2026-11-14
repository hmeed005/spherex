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
  const TIMEOUT_MS = 10 * 60 * 1000;  // 1er calcul d'une cible : peut prendre plusieurs minutes
  // Cibles démo connues du backend (position corrigée du mouvement propre)
  const KNOWN_TARGETS = [
    [/barnard/i, "barnard"],
    [/wise\s*j?0855/i, "wise 0855-0714"],
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
    let txt = parts.join(" · ");
    // Changement de groupe signalé directement dans la case affichée par le frontend
    if (e.group_changed) txt += `  ⚠ nouveau groupe : ${e.segment_label || e.group || ""}`;
    else if (e.disagreement) txt += `  • ${e.segment_label || e.group || ""}`;
    return txt;
  }

  async function fetchObservations({ ra, dec, fov, band, target } = {}) {
    if (ra === undefined || dec === undefined || ra === null || dec === null) {
      throw new Error("Coordonnées RA/Dec manquantes.");
    }
    const size = Math.min(MAX_FOV_ARCMIN, Math.max(1, Number(fov) || 6));
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

    // Le 1er calcul d'une cible prend plusieurs minutes : afficher le temps écoulé
    const statusEl = document.getElementById("timeline-status");
    const label = target?.shortName || target?.name || `RA ${ra}, Dec ${dec}`;
    const t0 = Date.now();
    const progress = setInterval(() => {
      if (!statusEl || !statusEl.classList.contains("loading")) return;
      const s = Math.round((Date.now() - t0) / 1000);
      statusEl.textContent =
        `Calcul SPHEREx en cours pour ${label}… ${s} s ` +
        `(le premier calcul d'une cible peut prendre plusieurs minutes, ensuite c'est instantané)`;
    }, 1000);

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
    let res;
    try {
      res = await fetch(`${API_BASE}/api/motion?${params}`, { signal: ctrl.signal });
    } catch (err) {
      if (err.name === "AbortError") throw new Error("Le backend met trop de temps à répondre.");
      throw new Error(`Backend injoignable (${API_BASE}). Le serveur est-il lancé ?`);
    } finally {
      clearTimeout(timer);
      clearInterval(progress);
    }
    if (!res.ok) {
      let detail = "";
      try { detail = JSON.stringify((await res.json()).detail); } catch (_) {}
      throw new Error(`Erreur backend ${res.status} ${detail}`);
    }

    const data = await res.json();
    const seq = data?.display?.sequences?.[0];
    const video = seq?.video;
    const timeline = video?.timeline || [];
    const fovLabel = `${size} arcmin`;

    const frames = timeline.map((e) => ({
      date: formatDate(e.date_utc),
      band: formatBand(e),
      imageUrl: absUrl(e.image_url),
      fov: fovLabel,
      // --- extras pour la synchronisation vidéo / la case de détails ---
      videoTime: e.seek_s,
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
      frames,
      targetLabel: data?.target_label || target?.name || "",
      summary: data?.display?.summary || "",
      motion: data?.motion || null,
      video: video
        ? {
            mp4: absUrl(video.mp4),
            mp4Markers: absUrl(video.mp4_markers),
            durationS: video.duration_s,
            width: video.width,
            height: video.height,
          }
        : null,
      raw: data,
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

  window.ObservationsApi = { fetchObservations, indexAtTime, API_BASE };
})();
