document.addEventListener("DOMContentLoaded", () => {
  // =========================================================
  // 1. Authoritative SPHEREx Multi-Galaxy & 3D Dwarf Catalog
  // =========================================================
  const SPHEREX_GALAXIES = [
    {
      id: "milky-way",
      name: "Milky Way",
      shortName: "Milky Way",
      type: "Barred Spiral (SBbc)",
      distanceLabel: "0 ly (Home)",
      style: "spiral-gold-blue",
      pos3D: { x: 0, y: 0, z: 0 },
      radius3D: 215,
      tiltX: 0.0,
      tiltY: 0.0,
      spinSpeed: 0.045,
      focusZoom: 1.15,
    },
    {
      id: "andromeda",
      name: "Andromeda (M31)",
      shortName: "Andromeda M31",
      type: "Grand Spiral (SA(s)b)",
      distanceLabel: "2.54 Mly",
      style: "spiral-gold-blue",
      pos3D: { x: 370, y: -230, z: 95 },
      radius3D: 185,
      tiltX: 0.58,
      tiltY: -0.32,
      spinSpeed: -0.036,
      focusZoom: 1.35,
    },
    {
      id: "lmc",
      name: "Large Magellanic Cloud",
      shortName: "LMC",
      type: "Magellanic Spiral (SB(s)m)",
      distanceLabel: "163,000 ly",
      style: "magellanic-irregular",
      pos3D: { x: -245, y: 210, z: -135 },
      radius3D: 115,
      tiltX: -0.45,
      tiltY: 0.28,
      spinSpeed: 0.06,
      focusZoom: 1.75,
    },
    {
      id: "triangulum",
      name: "Triangulum (M33)",
      shortName: "Triangulum M33",
      type: "Unbarred Spiral (SA(s)cd)",
      distanceLabel: "2.73 Mly",
      style: "spiral-blue-hii",
      pos3D: { x: 430, y: 245, z: -70 },
      radius3D: 135,
      tiltX: -0.38,
      tiltY: 0.42,
      spinSpeed: 0.05,
      focusZoom: 1.6,
    },
    {
      id: "sombrero",
      name: "Sombrero (M104)",
      shortName: "Sombrero M104",
      type: "Dust-Ring Spiral (SA(s)a)",
      distanceLabel: "29.3 Mly",
      style: "sombrero-dust-ring",
      pos3D: { x: -420, y: -240, z: 120 },
      radius3D: 150,
      tiltX: 0.24,
      tiltY: 0.2,
      spinSpeed: 0.032,
      focusZoom: 1.5,
    },
    {
      id: "whirlpool",
      name: "Whirlpool (M51)",
      shortName: "Whirlpool M51",
      type: "Interacting Spiral (SA(s)bc)",
      distanceLabel: "23.2 Mly",
      style: "spiral-blue-hii",
      pos3D: { x: -65, y: -420, z: -110 },
      radius3D: 140,
      tiltX: 0.42,
      tiltY: -0.25,
      spinSpeed: 0.042,
      focusZoom: 1.55,
    },
  ];

  const DWARF_TARGETS = [
    {
      id: "wise-0855",
      galaxyId: "milky-way",
      name: "WISE J085510.83−071442.5",
      shortName: "WISE 0855",
      type: "Y-Type Ultra-Cold Brown Dwarf",
      spectral: "Y0",
      temp: "250 K (−23°C)",
      distanceLy: "7.43 ly",
      distanceKm: "7.03 × 10¹³ km",
      velocityKms: "91.4 km/s",
      velocityNum: 91.4,
      velocityKmh: "329,040 km/h",
      velComponents: "Vt 87.2 | Vr −27.4 km/s",
      properMotion: "8,130 mas/yr",
      properMotionNum: 8130,
      trajPerYearKm: "2.88 × 10⁹ km/yr",
      trajPerYearBillions: 2.88,
      trajPerEpochKm: "+1.44B km / 6-mo",
      mass: "3–10 M_Jup",
      radiusKm: "~69,900 km",
      constellation: "HYDRA",
      discovery: "2014 (NASA WISE)",
      age: "~3–8 Gyr",
      flag: "FLAGS: 0x00 NOMINAL",
      ra: "133.7951",
      dec: "-7.2451",
      local3D: { x: -78, y: -56, z: 24 },
      velVec3D: { x: 0.78, y: -0.46, z: 0.42 },
      trajSpan3D: 54,
      simMode: "parallax-drift",
      summary:
        "WISE 0855 is a Y0-type ultra-cold brown dwarf located 7.43 light-years away in Hydra with an effective temperature of 250 K (−23°C). Discovered in 2014 by NASA WISE, it travels at 91.4 km/s in 3D space, covering 2.88 × 10⁹ km per year.",
      desc: "Coldest known substellar brown dwarf outside our Solar System. Travels 2.88 billion km every year across the 3D solar neighborhood.",
      motionPerEpoch: { dx: 19, dy: -12, pulse: 0 },
      spectrumProfile: [0.18, 0.25, 0.12, 0.35, 0.14, 0.42, 0.22, 0.15, 0.68, 0.92, 0.85, 0.55],
    },
    {
      id: "barnards-star",
      galaxyId: "milky-way",
      name: "Barnard's Star (GJ 699)",
      shortName: "Barnard's Star",
      type: "High-Velocity Halo Red Dwarf",
      spectral: "M4Ve",
      temp: "3,134 K",
      distanceLy: "5.96 ly",
      distanceKm: "5.64 × 10¹³ km",
      velocityKms: "142.7 km/s",
      velocityNum: 142.7,
      velocityKmh: "513,720 km/h",
      velComponents: "Vt 90.1 | Vr −110.6 km/s",
      properMotion: "10,358 mas/yr",
      properMotionNum: 10358,
      trajPerYearKm: "4.50 × 10⁹ km/yr",
      trajPerYearBillions: 4.5,
      trajPerEpochKm: "+2.25B km / 6-mo",
      mass: "0.16 M_☉",
      radiusKm: "~136,300 km",
      constellation: "OPHIUCHUS",
      discovery: "1916 (E.E. Barnard)",
      age: "~10 Gyr (Halo)",
      flag: "FLAGS: 0x00 NOMINAL",
      ra: "269.4521",
      dec: "4.6934",
      local3D: { x: -18, y: -88, z: 36 },
      velVec3D: { x: -0.58, y: -0.64, z: 0.5 },
      trajSpan3D: 62,
      simMode: "parallax-drift",
      summary:
        "Barnard's Star (GJ 699) is an ancient M4Ve halo red dwarf 5.96 light-years away in Ophiuchus. Moving at 142.7 km/s on a steep 3D galactic halo inclination (10,358 mas/yr), it displaces by +2.25B km every 6-month SPHEREx scan.",
      desc: "Fastest proper-motion star in Earth's sky (10.36 arcsec/yr), plunging steeply through the Galactic plane at 142.7 km/s.",
      motionPerEpoch: { dx: -15, dy: -17, pulse: 0 },
      spectrumProfile: [0.62, 0.78, 0.88, 0.95, 0.91, 0.84, 0.76, 0.68, 0.59, 0.52, 0.46, 0.41],
    },
    {
      id: "epsilon-indi-b",
      galaxyId: "milky-way",
      name: "Epsilon Indi Ba / Bb",
      shortName: "Epsilon Indi B",
      type: "Resolved Binary Brown Dwarf",
      spectral: "T1 + T6",
      temp: "1,280 K / 850 K",
      distanceLy: "11.87 ly",
      distanceKm: "1.12 × 10¹⁴ km",
      velocityKms: "86.5 km/s",
      velocityNum: 86.5,
      velocityKmh: "311,400 km/h",
      velComponents: "Vt 80.8 | Vr −31.0 km/s",
      properMotion: "4,704 mas/yr",
      properMotionNum: 4704,
      trajPerYearKm: "2.73 × 10⁹ km/yr",
      trajPerYearBillions: 2.73,
      trajPerEpochKm: "+1.36B km / 6-mo",
      mass: "47 + 28 M_Jup",
      radiusKm: "~64,000 km",
      constellation: "INDUS",
      discovery: "2003 (Scholz et al.)",
      age: "~3.5 Gyr",
      flag: "FLAGS: 0x02 BLENDED_PSF",
      ra: "330.8402",
      dec: "-56.7861",
      local3D: { x: 74, y: 42, z: -28 },
      velVec3D: { x: 0.74, y: 0.58, z: -0.34 },
      trajSpan3D: 50,
      simMode: "binary-orbit",
      summary:
        "Epsilon Indi Ba / Bb is a gravitationally bound T1 + T6 binary brown dwarf system 11.87 light-years distant in Indus. The pair carries a combined mass of 47 + 28 M_Jup and travels at 86.5 km/s along a 2.73 × 10⁹ km/yr 3D trajectory.",
      desc: "Gravitationally bound pair of T-dwarfs separated by 395 million km (2.65 AU), orbiting each other in 3D while racing at 86.5 km/s.",
      motionPerEpoch: { dx: 12, dy: 9, pulse: 0 },
      spectrumProfile: [0.35, 0.52, 0.28, 0.65, 0.31, 0.72, 0.44, 0.26, 0.79, 0.84, 0.62, 0.48],
    },
    {
      id: "rw-aurigae",
      galaxyId: "milky-way",
      name: "RW Aurigae A/B",
      shortName: "RW Aurigae",
      type: "Classical T Tauri Variable",
      spectral: "K0Ve + K5",
      temp: "5,080 K",
      distanceLy: "530 ly",
      distanceKm: "5.01 × 10¹⁵ km",
      velocityKms: "23.8 km/s",
      velocityNum: 23.8,
      velocityKmh: "85,680 km/h",
      velComponents: "Vt 16.4 | Vr +17.2 km/s",
      properMotion: "21.4 mas/yr",
      properMotionNum: 21.4,
      trajPerYearKm: "7.51 × 10⁸ km/yr",
      trajPerYearBillions: 0.751,
      trajPerEpochKm: "+375M km / 6-mo",
      mass: "1.4 + 0.9 M_☉",
      radiusKm: "~1,180,000 km",
      constellation: "AURIGA",
      discovery: "1906 (L. Ceraski)",
      age: "~8 Myr (Young)",
      flag: "FLAGS: 0x04 FLUX_VAR",
      ra: "76.9565",
      dec: "30.4014",
      local3D: { x: -58, y: 76, z: -14 },
      velVec3D: { x: 0.48, y: 0.84, z: -0.24 },
      trajSpan3D: 42,
      simMode: "dust-pulsation",
      summary:
        "RW Aurigae A/B is a young (~8 Myr) classical T Tauri binary system 530 light-years away in Auriga. Flagged for infrared flux variability (FLAGS: 0x04 FLUX_VAR), it moves at 23.8 km/s while warped circumstellar dust drives brightness dips.",
      desc: "Young pre-main-sequence binary undergoing irregular infrared dimming events caused by warped circumstellar dust streams.",
      motionPerEpoch: { dx: 0, dy: 0, pulse: 0.55 },
      spectrumProfile: [0.48, 0.56, 0.64, 0.71, 0.76, 0.81, 0.85, 0.89, 0.92, 0.95, 0.93, 0.9],
    },
    {
      id: "r-draconis",
      galaxyId: "milky-way",
      name: "R Draconis (HD 149880)",
      shortName: "R Draconis",
      type: "Mira Long-Period Variable",
      spectral: "M5e–M9e",
      temp: "2,450 K",
      distanceLy: "1,490 ly",
      distanceKm: "1.41 × 10¹⁶ km",
      velocityKms: "138.2 km/s",
      velocityNum: 138.2,
      velocityKmh: "497,520 km/h",
      velComponents: "Vt 32.1 | Vr −134.4 km/s",
      properMotion: "14.8 mas/yr",
      properMotionNum: 14.8,
      trajPerYearKm: "4.36 × 10⁹ km/yr",
      trajPerYearBillions: 4.36,
      trajPerEpochKm: "+2.18B km / 6-mo",
      mass: "~1.1 M_☉",
      radiusKm: "~1.95 × 10⁸ km",
      constellation: "DRACO",
      discovery: "1876 (H. Geelmuyden)",
      age: "~6 Gyr (AGB)",
      flag: "FLAGS: 0x04 FLUX_VAR",
      ra: "248.1654",
      dec: "66.7542",
      local3D: { x: 26, y: 84, z: 42 },
      velVec3D: { x: -0.32, y: -0.76, z: 0.56 },
      trajSpan3D: 48,
      simMode: "dust-pulsation",
      summary:
        "R Draconis (HD 149880) is an asymptotic giant branch Mira variable at 1,490 light-years in Draco. Reaching ~1.95 × 10⁸ km in radius at 2,450 K, it travels at 138.2 km/s with a radial velocity of −134.4 km/s.",
      desc: "Asymptotic giant branch Mira pulsator expanding up to 195 million km in radius and varying by >6 magnitudes every 245.5 days.",
      motionPerEpoch: { dx: 0, dy: 0, pulse: 0.65 },
      spectrumProfile: [0.42, 0.58, 0.45, 0.79, 0.52, 0.91, 0.86, 0.72, 0.95, 0.88, 0.77, 0.69],
    },
    {
      id: "planet-x-cand",
      galaxyId: "milky-way",
      name: "TNO / Planet X Candidate",
      shortName: "Planet X Cand.",
      type: "Outer Solar System Perturber",
      spectral: "Ice/Tholin",
      temp: "~42 K (−231°C)",
      distanceLy: "480 AU (0.0076 ly)",
      distanceKm: "7.18 × 10¹⁰ km",
      velocityKms: "4.29 km/s",
      velocityNum: 4.29,
      velocityKmh: "15,444 km/h",
      velComponents: "V_orb 4.25 | Vr +0.58 km/s",
      properMotion: "1,120 mas/yr",
      properMotionNum: 1120,
      trajPerYearKm: "1.35 × 10⁸ km/yr",
      trajPerYearBillions: 0.135,
      trajPerEpochKm: "+67.6M km / 6-mo",
      mass: "~6.2 M_⊕",
      radiusKm: "~19,500 km",
      constellation: "TAURUS / ORION",
      discovery: "SPHEREx Search Target",
      age: "4.5 Gyr (Primordial)",
      flag: "FLAGS: 0x08 MOVING_TNO",
      ra: "52.4120",
      dec: "18.2045",
      local3D: { x: 108, y: -52, z: 16 },
      velVec3D: { x: 0.82, y: 0.52, z: 0.24 },
      trajSpan3D: 48,
      simMode: "tno-arc",
      summary:
        "TNO / Planet X Candidate is a ~6.2 M_⊕ outer Solar System target modeled at 480 AU (7.18 × 10¹⁰ km) toward Taurus / Orion. Moving at 4.29 km/s (1,120 mas/yr), it advances by +67.6M km per 6-month SPHEREx observation window.",
      desc: "Hypothetical super-Earth orbiting at 71.8 billion km from the Sun, detectable via reflexive Earth-orbit parallax and thermal IR glow.",
      motionPerEpoch: { dx: 10, dy: 7, pulse: 0.1 },
      spectrumProfile: [0.15, 0.19, 0.24, 0.29, 0.22, 0.34, 0.45, 0.58, 0.74, 0.88, 0.95, 0.91],
    },
  ];

  // F1 Verified Target Presets (Target A, Target B, Target C)
  const VERIFIED_TARGET_PRESETS = {
    "target-a": DWARF_TARGETS[0], // WISE 0855
    "target-b": DWARF_TARGETS[1], // Barnard's Star
    "target-c": DWARF_TARGETS[2], // Epsilon Indi B
  };

  const galaxyMap = new Map(SPHEREX_GALAXIES.map((g) => [g.id, g]));

  function getTargetWorld3D(target) {
    const g = galaxyMap.get(target.galaxyId) || SPHEREX_GALAXIES[0];
    return {
      x: g.pos3D.x + target.local3D.x,
      y: g.pos3D.y + target.local3D.y,
      z: g.pos3D.z + target.local3D.z,
      planeZ: g.pos3D.z,
    };
  }

  // =========================================================
  // 2. DOM References
  // =========================================================
  const dwarfSidebar = document.getElementById("dwarf-sidebar");
  const mobileDrawerToggle = document.getElementById("mobile-drawer-toggle");
  const mobileDrawerLabel = document.getElementById("mobile-drawer-label");
  const liveUtcClock = document.getElementById("live-utc-clock");
  const presetPills = Array.from(document.querySelectorAll(".preset-pill"));
  const catalogSectionTitle = document.getElementById("catalog-section-title");
  const dwarfListScroll = document.getElementById("dwarf-list-scroll");

  const galaxyStage = document.getElementById("galaxy-stage");
  const skyCanvas = document.getElementById("sky-canvas");
  const skyCtx = skyCanvas.getContext("2d");
  const trajCameraGroup = document.getElementById("trajectory-camera-group");

  const backToGalaxyBtn = document.getElementById("back-to-galaxy-btn");
  const openAnimModalBtn = document.getElementById("open-anim-modal-btn");
  const openCompareModalBtn = document.getElementById("open-compare-modal-btn");
  const inspectorAnimTrigger = document.getElementById("inspector-anim-trigger");
  const inspectorCompareTrigger = document.getElementById("inspector-compare-trigger");

  const form = document.getElementById("coordinate-form");
  const raInput = document.getElementById("ra-input");
  const decInput = document.getElementById("dec-input");

  // RA / Dec toujours écrits avec un point (champ texte : le navigateur ne les affiche plus
  // à la française « 133,7951 ») ; une virgule tapée par l'utilisateur devient un point.
  [raInput, decInput, document.getElementById("fov-select")].forEach((inp) => {
    inp?.addEventListener("input", () => {
      if (inp.value.includes(",")) {
        const pos = inp.selectionStart;
        inp.value = inp.value.replace(/,/g, ".");
        try { inp.setSelectionRange(pos, pos); } catch (_) {}
      }
    });
  });
  const fovSelect = document.getElementById("fov-select");
  // FOV : liste de valeurs ; « Autre… » affiche un champ pour taper sa propre valeur (1 à 12')
  const fovPreset = document.getElementById("fov-preset");
  const fovUnit = document.querySelector(".fov-unit");
  fovPreset?.addEventListener("change", () => {
    const custom = fovPreset.value === "custom";
    fovSelect.classList.toggle("is-hidden", !custom);
    fovUnit?.classList.toggle("is-hidden", !custom);
    if (custom) {
      fovSelect.focus();
      fovSelect.select();
    } else {
      fovSelect.value = fovPreset.value;
    }
  });
  const detectorSelect = document.getElementById("detector-select");
  const formError = document.getElementById("form-error");

  // 3D Camera Controls
  const camZoomReadout = document.getElementById("cam-zoom-readout");
  const camPreset3d = document.getElementById("cam-preset-3d");
  const camPresetTop = document.getElementById("cam-preset-top");
  const camPresetEdge = document.getElementById("cam-preset-edge");
  const camAutorotateBtn = document.getElementById("cam-autorotate-btn");
  const camZoomOutBtn = document.getElementById("cam-zoom-out");
  const camZoomSlider = document.getElementById("cam-zoom-slider");
  const camZoomInBtn = document.getElementById("cam-zoom-in");
  const camResetBtn = document.getElementById("cam-reset-btn");
  const liveRealtimeDrift = document.getElementById("live-realtime-drift");

  // Tooltip
  const tooltip = document.getElementById("dwarf-tooltip");
  const tooltipName = document.getElementById("tooltip-name");
  const tooltipSpec = document.getElementById("tooltip-spec");
  const tooltipGalaxy = document.getElementById("tooltip-galaxy");
  const tooltipType = document.getElementById("tooltip-type");
  const tooltipCoords = document.getElementById("tooltip-coords");
  const tooltipMetrics = document.getElementById("tooltip-metrics");
  const tooltipKinematics = document.getElementById("tooltip-kinematics");
  const tooltipHint = document.getElementById("tooltip-hint");

  // Detail Inspector (F2)
  const inspector = document.getElementById("target-inspector");
  const closeInspectorBtn = document.getElementById("close-inspector");
  const inspBadge = document.getElementById("insp-badge");
  // étiquette « FLAGS » (code inventé) retirée : élément invisible pour le reste du code
  const inspFlag = document.getElementById("insp-flag") || document.createElement("span");
  const inspTitle = document.getElementById("insp-title");
  const inspDesignation = document.getElementById("insp-designation");
  const inspSummary = document.getElementById("insp-summary");
  const FAMOUS_STARS = new Set(["wise-0855", "barnards-star", "epsilon-indi-b", "rw-aurigae", "r-draconis"]);

  // Sections « 3D Identity & Astrometry », « Physical Properties » et « Discovery & Survey
  // Metadata » retirées (valeurs de catalogue, pas des données SPHEREx) : leurs champs
  // pointent vers des éléments invisibles pour que le reste du code continue de marcher.
  const detOrDummy = (id) => document.getElementById(id) || document.createElement("span");
  const detGalaxy = detOrDummy("det-galaxy");
  const detType = detOrDummy("det-type");
  const detSpectral = detOrDummy("det-spectral");
  const detConstellation = detOrDummy("det-constellation");
  const detCoords = detOrDummy("det-coords");
  const detXyz3d = detOrDummy("det-xyz-3d");

  const detTemp = detOrDummy("det-temp");
  const detDistKm = detOrDummy("det-dist-km");
  const detDistLy = detOrDummy("det-dist-ly");
  const detMass = detOrDummy("det-mass");
  const detRadius = detOrDummy("det-radius");
  const detAge = detOrDummy("det-age");

  const detVelKms = detOrDummy("det-vel-kms");
  const detVelKmh = detOrDummy("det-vel-kmh");
  const detTrajYr = detOrDummy("det-traj-yr");
  const detTrajEpoch = detOrDummy("det-traj-epoch");
  const detLiveKm = detOrDummy("det-live-km");
  const detVelComp = detOrDummy("det-vel-comp");
  const detPm = detOrDummy("det-pm");

  const detDiscovery = detOrDummy("det-discovery");
  const detFlag = detOrDummy("det-flag");
  const detBandFov = detOrDummy("det-band-fov");
  const inspDesc = detOrDummy("insp-desc");

  const cutoutViewerBox = document.getElementById("cutout-viewer-box");
  const diffModeBtn = document.getElementById("diff-mode-btn");
  const cutoutFullscreenBtn = document.getElementById("cutout-fullscreen-btn");
  const cutoutEpochLabel = document.getElementById("cutout-epoch-label");
  const cutoutFovLabel = document.getElementById("cutout-fov-label");
  const cutoutImg = document.getElementById("cutout-img");
  const cutoutVideo = document.getElementById("cutout-video"); // vidéo MP4 du backend
  const markerCanvas = document.getElementById("cutout-marker-canvas"); // repère de la cible
  const markerToggleBtn = document.getElementById("marker-toggle-btn");
  const groupPicker = document.getElementById("group-picker");      // choix du groupe à regarder
  const groupSelect = document.getElementById("group-select");
  const groupInfoEl = document.getElementById("group-info");   // retiré de l'interface
  const groupCardsEl = document.getElementById("group-cards");
  const groupAlertEl = document.getElementById("group-alert");
  const cutoutCanvas = document.getElementById("cutout-canvas");
  const cutoutCtx = cutoutCanvas.getContext("2d");
  const spectrumCanvas = document.getElementById("spectrum-canvas") || document.createElement("canvas"); // spectre inventé retiré
  const spectrumCtx = spectrumCanvas.getContext("2d");

  // F3 Timeline Elements
  const statusEl = document.getElementById("timeline-status");
  const bodyEl = document.getElementById("timeline-controls-body");
  const badgeEl = document.getElementById("epoch-badge");
  const dateEl = document.getElementById("epoch-date");
  const bandEl = document.getElementById("epoch-band");
  const epochNoteEl = document.getElementById("epoch-note");
  const roDateEl = document.getElementById("ro-date");
  const roDetEl = document.getElementById("ro-det");
  const roWlEl = document.getElementById("ro-wl");

  // valeur bien visible sous la vidéo ; petit éclair quand elle change
  function setReadout(el, text) {
    if (!el) return;
    const t = text || "—";
    if (el.textContent !== t) {
      el.textContent = t;
      el.classList.remove("changed");
      void el.offsetWidth;                // relance l'animation
      el.classList.add("changed");
    }
  }
  const prevBtn = document.getElementById("btn-prev");
  const playBtn = document.getElementById("btn-play");
  const pauseBtn = document.getElementById("btn-pause");
  const nextBtn = document.getElementById("btn-next");
  const slider = document.getElementById("epoch-slider");
  const ticksEl = document.getElementById("epoch-ticks");

  // Pop-up 1: 3D Trajectory & Auto-Follow Modal Elements
  const animModalBackdrop = document.getElementById("anim-modal-backdrop");
  const closeAnimModalBtn = document.getElementById("close-anim-modal");
  const modalGalaxySubtitle = document.getElementById("modal-galaxy-subtitle");
  const modalDwarfTitle = document.getElementById("modal-dwarf-title");
  const modalSimCanvas = document.getElementById("modal-sim-canvas");
  const modalSimCtx = modalSimCanvas.getContext("2d");
  const hudSimYear = document.getElementById("hud-sim-year");
  const hudSimKm = document.getElementById("hud-sim-km");
  const hudSimVel = document.getElementById("hud-sim-vel");
  const hudSimZoom = document.getElementById("hud-sim-zoom");
  const modalPlayBtn = document.getElementById("modal-play-btn");
  const modalDirBtn = document.getElementById("modal-dir-btn");
  const modalResetBtn = document.getElementById("modal-reset-btn");
  const modalFollowBtn = document.getElementById("modal-follow-btn");
  const modalRecenterBtn = document.getElementById("modal-recenter-btn");
  const speedPills = Array.from(document.querySelectorAll(".speed-pill"));
  const modalSpeedSlider = document.getElementById("modal-speed-slider");
  const modalSpeedReadout = document.getElementById("modal-speed-readout");
  const zoomPills = Array.from(document.querySelectorAll(".zoom-pill"));
  const modalZoomSlider = document.getElementById("modal-zoom-slider");
  const modalZoomReadout = document.getElementById("modal-zoom-readout");
  const view3dPills = Array.from(document.querySelectorAll(".view3d-pill"));
  const modalTimeSlider = document.getElementById("modal-time-slider");
  const modalYearReadout = document.getElementById("modal-year-readout");
  const chkSimVector = document.getElementById("chk-sim-vector");
  const chkSimParallax = document.getElementById("chk-sim-parallax");
  const chkSimTrail = document.getElementById("chk-sim-trail");
  const chkSimGrid = document.getElementById("chk-sim-grid");

  // Pop-up 2 (F2): Two-Date Side-by-Side Comparison Modal Elements
  const compareModalBackdrop = document.getElementById("compare-modal-backdrop");
  const closeCompareModalBtn = document.getElementById("close-compare-modal");
  const compareModalTitle = document.getElementById("compare-modal-title");
  const compareSelectA = document.getElementById("compare-select-a");
  const compareSelectB = document.getElementById("compare-select-b");
  const compareImgA = document.getElementById("compare-img-a");
  const compareImgB = document.getElementById("compare-img-b");
  const compareMetaDateA = document.getElementById("compare-meta-date-a");
  const compareMetaBandA = document.getElementById("compare-meta-band-a");
  const compareMetaFovA = document.getElementById("compare-meta-fov-a");
  const compareMetaDateB = document.getElementById("compare-meta-date-b");
  const compareMetaBandB = document.getElementById("compare-meta-band-b");
  const compareMetaFovB = document.getElementById("compare-meta-fov-b");

  // =========================================================
  // 3. Motion Preference & Cubic-Bezier(0.22, 1, 0.36, 1) Solver
  // =========================================================
  const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  let prefersReducedMotion = reducedMotionQuery.matches;
  reducedMotionQuery.addEventListener("change", (e) => {
    prefersReducedMotion = e.matches;
  });

  function cubicBezierEaseOut(t) {
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    const x1 = 0.22, y1 = 1.0, x2 = 0.36, y2 = 1.0;
    const sampleX = (u) =>
      3 * (1 - u) * (1 - u) * u * x1 + 3 * (1 - u) * u * u * x2 + u * u * u;
    const sampleY = (u) =>
      3 * (1 - u) * (1 - u) * u * y1 + 3 * (1 - u) * u * u * y2 + u * u * u;

    let lo = 0, hi = 1, u = t;
    for (let i = 0; i < 14; i++) {
      u = (lo + hi) * 0.5;
      const x = sampleX(u);
      if (x < t) lo = u;
      else hi = u;
    }
    return sampleY(u);
  }

  // =========================================================
  // 4. Visual Encoding & Coordinate Formatting Helpers
  // =========================================================
  const ACCENT_AMBER = { hex: "#e89b48", rgb: "232, 155, 72", isHighVel: true };
  const ACCENT_TEAL = { hex: "#38b2ac", rgb: "56, 178, 172", isHighVel: false };

  function getEncodingForTarget(target) {
    const vel = typeof target.velocityNum === "number" ? target.velocityNum : 0;
    const palette = vel >= 80 ? ACCENT_AMBER : ACCENT_TEAL;
    const pm = typeof target.properMotionNum === "number" ? target.properMotionNum : 100;
    const norm = Math.min(1, Math.max(0, (Math.log10(Math.max(10, pm)) - 1.1) / 3.0));
    const baseRadius = 4.6 + norm * 4.8;
    return { ...palette, baseRadius };
  }

  function formatRaHms(raDegStr) {
    const deg = Number.parseFloat(raDegStr);
    if (!Number.isFinite(deg)) return "";
    const totalHours = deg / 15;
    const h = Math.floor(totalHours);
    const mFloat = (totalHours - h) * 60;
    const m = Math.floor(mFloat);
    const s = ((mFloat - m) * 60).toFixed(1);
    return `${String(h).padStart(2, "0")}h ${String(m).padStart(2, "0")}m ${s.padStart(4, "0")}s`;
  }

  function formatDecDms(decDegStr) {
    const deg = Number.parseFloat(decDegStr);
    if (!Number.isFinite(deg)) return "";
    const sign = deg < 0 ? "−" : "+";
    const abs = Math.abs(deg);
    const d = Math.floor(abs);
    const mFloat = (abs - d) * 60;
    const m = Math.floor(mFloat);
    const s = Math.round((mFloat - m) * 60);
    return `${sign}${String(d).padStart(2, "0")}° ${String(m).padStart(2, "0")}′ ${String(s).padStart(2, "0")}″`;
  }

  // =========================================================
  // 5. F1 Verified Target Presets, Multi-Galaxy & Dwarf Catalog
  // =========================================================
  // une seule vue : l'univers en général (plus de choix ni de noms de galaxies)
  let activeGalaxyId = "all";
  let selectedTarget = null;
  let hoveredTarget = null;
  let customTrackedTarget = null;
  let diffSubtractionMode = false;

  function syncPresetPills(target) {
    presetPills.forEach((pill) => {
      const presetTarget = VERIFIED_TARGET_PRESETS[pill.dataset.preset];
      const active = Boolean(target && presetTarget && presetTarget.id === target.id);
      pill.classList.toggle("is-active", active);
      pill.setAttribute("aria-pressed", String(active));
    });
  }

  presetPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const presetTarget = VERIFIED_TARGET_PRESETS[pill.dataset.preset];
      if (!presetTarget) return;
      dwarfSidebar.classList.remove("is-drawer-open");
      mobileDrawerToggle.setAttribute("aria-expanded", "false");
      selectAndZoomToTarget(presetTarget);
    });
  });

  function getAllTargets() {
    return customTrackedTarget
      ? [...DWARF_TARGETS, customTrackedTarget]
      : DWARF_TARGETS;
  }

  function getFilteredTargets() {
    const all = getAllTargets();
    if (activeGalaxyId === "all") return all;
    return all.filter((t) => t.galaxyId === activeGalaxyId);
  }

  function renderGalaxySwitcher() {
    // plus de sélecteur de galaxies : l'univers est montré en entier, sans noms
    activeGalaxyId = "all";
    if (catalogSectionTitle) catalogSectionTitle.textContent = "OBJETS À SUIVRE";
  }

  function setActiveGalaxy(galId) {
    activeGalaxyId = galId;
    renderGalaxySwitcher();

    if (selectedTarget && galId !== "all" && selectedTarget.galaxyId !== galId) {
      returnToGalaxyView(false);
    }

    renderSideList();

    if (!selectedTarget) {
      if (galId === "all") {
        flyCamera3D({
          focusX: 0,
          focusY: 0,
          focusZ: 0,
          zoom: 0.62,
          yaw: 0.32,
          pitch: 1.02,
          panX: 0,
          panY: 0,
          dim: 0,
        });
      } else {
        const g = galaxyMap.get(galId) || SPHEREX_GALAXIES[0];
        flyCamera3D({
          focusX: g.pos3D.x,
          focusY: g.pos3D.y,
          focusZ: g.pos3D.z,
          zoom: g.focusZoom || 1.2,
          yaw: 0.25,
          pitch: 1.04,
          panX: 0,
          panY: 0,
          dim: 0,
        });
      }
    }
  }

  function renderSideList() {
    const list = getFilteredTargets();
    dwarfListScroll.innerHTML = "";

    list.forEach((target) => {
      const enc = getEncodingForTarget(target);
      const isSelected = selectedTarget?.id === target.id;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `dwarf-row${isSelected ? " is-selected" : ""}`;
      btn.setAttribute("role", "option");
      btn.setAttribute("aria-selected", String(isSelected));
      btn.dataset.targetId = target.id;

      const velClass = enc.isHighVel ? "is-high-vel" : "is-low-vel";
      btn.innerHTML = `
        <div class="dwarf-row-top">
          <div class="dwarf-row-name-wrap">
            <span class="dwarf-dot ${velClass}" aria-hidden="true"></span>
            <span class="dwarf-row-name">${target.shortName || target.name}</span>
          </div>
          <span class="dwarf-row-stat ${velClass}">${target.velocityKms}</span>
        </div>
        <div class="dwarf-row-meta">
          <span>${target.spectral} • ${target.distanceLy}</span>
          <span>${target.constellation}</span>
        </div>
      `;

      btn.addEventListener("click", () => {
        dwarfSidebar.classList.remove("is-drawer-open");
        mobileDrawerToggle.setAttribute("aria-expanded", "false");
        selectAndZoomToTarget(target);
      });

      dwarfListScroll.appendChild(btn);
    });

    mobileDrawerLabel.textContent = selectedTarget
      ? `${selectedTarget.shortName || selectedTarget.name} (${list.length})`
      : `Universe (${list.length})`;
  }

  mobileDrawerToggle.addEventListener("click", () => {
    const open = dwarfSidebar.classList.toggle("is-drawer-open");
    mobileDrawerToggle.setAttribute("aria-expanded", String(open));
  });

  // =========================================================
  // 6. Photorealistic Galaxy Texture Synthesizer (FBM Dust Lanes)
  // =========================================================
  const galaxyTextures = {};

  function seededRand(seed) {
    const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453123;
    return x - Math.floor(x);
  }

  const PERM = new Uint8Array(512);
  (() => {
    const p = new Uint8Array(256);
    for (let i = 0; i < 256; i++) p[i] = i;
    for (let i = 255; i > 0; i--) {
      const j = Math.floor(seededRand(i + 99) * (i + 1));
      const tmp = p[i];
      p[i] = p[j];
      p[j] = tmp;
    }
    for (let i = 0; i < 512; i++) PERM[i] = p[i & 255];
  })();

  function valueNoise2D(x, y) {
    const xi = Math.floor(x) & 255;
    const yi = Math.floor(y) & 255;
    const xf = x - Math.floor(x);
    const yf = y - Math.floor(y);
    const u = xf * xf * (3 - 2 * xf);
    const v = yf * yf * (3 - 2 * yf);

    const aa = PERM[PERM[xi] + yi] / 255;
    const ab = PERM[PERM[xi] + yi + 1] / 255;
    const ba = PERM[PERM[xi + 1] + yi] / 255;
    const bb = PERM[PERM[xi + 1] + yi + 1] / 255;

    const x1 = aa + u * (ba - aa);
    const x2 = ab + u * (bb - ab);
    return x1 + v * (x2 - x1);
  }

  function fbm5(x, y) {
    let sum = 0;
    let amp = 0.52;
    let freq = 1.0;
    for (let o = 0; o < 5; o++) {
      sum += amp * valueNoise2D(x * freq, y * freq);
      freq *= 2.08;
      amp *= 0.49;
    }
    return sum;
  }

  // teintes des galaxies de décor (multiplient les couleurs d'une spirale)
  const GALAXY_PALETTES = {
    "spiral-violet": [0.92, 0.7, 1.25],
    "spiral-rose": [1.15, 0.78, 0.9],
    "spiral-ice": [0.78, 0.95, 1.2],
  };

  function createGalaxyTexture(styleKey, size = 900) {
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    const imgData = ctx.createImageData(size, size);
    const data = imgData.data;
    const half = size * 0.5;

    for (let py = 0; py < size; py++) {
      const dy = (py - half) / half;
      for (let px = 0; px < size; px++) {
        const dx = (px - half) / half;
        const r2 = dx * dx + dy * dy;
        if (r2 >= 1.0) continue;

        const r = Math.sqrt(r2);
        const theta = Math.atan2(dy, dx);

        let red = 0, green = 0, blue = 0, alpha = 0;

        if (styleKey === "elliptical-warm" || styleKey === "elliptical-ice") {
          // galaxie elliptique : grand halo lisse, très lumineux au centre
          const ex = dx, ey = dy * 1.35;
          const re = Math.sqrt(ex * ex + ey * ey);
          if (re >= 1.0) continue;
          const lum = (Math.exp(-re * 7.5) * 1.5 + Math.exp(-re * 2.6) * 0.42) * (1 - Math.pow(re, 3));
          if (lum < 0.004) continue;
          const ice = styleKey === "elliptical-ice";
          red = 255 * (1 - Math.exp(-(lum * (ice ? 200 : 255)) / 140));
          green = 255 * (1 - Math.exp(-(lum * (ice ? 220 : 205)) / 145));
          blue = 255 * (1 - Math.exp(-(lum * (ice ? 255 : 150)) / 150));
          alpha = Math.min(255, 255 * (1 - Math.exp(-lum * 2.6)));
        } else if (styleKey === "sombrero-dust-ring") {
          const bulge = Math.exp(-r * 6.5) * 1.45 + Math.exp(-r * 2.8) * 0.45;
          const ringBand = Math.exp(-Math.pow((r - 0.66) / 0.14, 2));
          const dustTurb = fbm5(dx * 14.0 + 3.2, dy * 14.0 + 5.1);
          const dustRing = Math.exp(-Math.pow((r - 0.67) / 0.055, 2)) * (0.65 + 0.5 * dustTurb);
          const transmittance = Math.max(0.05, 1.0 - dustRing * 0.94);
          const lum = (bulge + ringBand * 0.62) * transmittance * (1 - Math.pow(r, 5));

          if (lum < 0.0035) continue;
          red = 255 * (1 - Math.exp(-(lum * 255) / 145));
          green = 255 * (1 - Math.exp(-(lum * 212) / 150));
          blue = 255 * (1 - Math.exp(-(lum * 165) / 155));
          alpha = Math.min(255, 255 * (1 - Math.exp(-lum * 2.8)));
        } else if (styleKey === "magellanic-irregular") {
          const barDx = dx * 0.95 + dy * 0.32;
          const barDy = -dx * 0.32 + dy * 0.95;
          const bar = Math.exp(-(barDx * barDx * 5.2 + barDy * barDy * 22.0)) * 0.95;
          const cloud = fbm5(dx * 7.5 + 4.1, dy * 7.5 + 2.8);
          const tarantula = Math.exp(-((dx - 0.24) ** 2 + (dy + 0.16) ** 2) * 38) * 1.25;
          const envelope = Math.exp(-r * 2.4) * (1 - Math.pow(r, 4));
          const lum = envelope * (bar + cloud * 0.85) + tarantula;

          if (lum < 0.004) continue;
          red = 255 * (1 - Math.exp(-(lum * 185 + tarantula * 140) / 150));
          green = 255 * (1 - Math.exp(-(lum * 215 + tarantula * 85) / 150));
          blue = 255 * (1 - Math.exp(-(lum * 250 + tarantula * 130) / 150));
          alpha = Math.min(255, 255 * (1 - Math.exp(-lum * 2.4)));
        } else {
          const warp = (fbm5(dx * 4.2 + 3.1, dy * 4.2 + 1.7) - 0.5) * 0.72;
          const spiralAngle = theta + 3.65 * Math.log(r + 0.05) + warp;

          const armPrimary = Math.pow(0.5 + 0.5 * Math.cos(2 * spiralAngle), 2.45);
          const armSpurs = Math.pow(0.5 + 0.5 * Math.cos(4 * spiralAngle + 0.9), 3.3) * 0.48;
          const armSignal = Math.min(1, armPrimary + armSpurs);

          const gasTurb = fbm5(dx * 10.5 + 7.2, dy * 10.5 + 4.8);
          const fineDetail = fbm5(dx * 25.0 + 1.4, dy * 25.0 + 9.3);

          const diskEnvelope = Math.exp(-r * 2.95) * (1 - Math.pow(r, 4));
          const bulgeScale = styleKey === "spiral-blue-hii" ? 0.95 : 1.45;
          const bulge = Math.exp(-r * 14.5) * bulgeScale + Math.exp(-r * 6.4) * 0.4;

          const dustShock = Math.pow(0.5 + 0.5 * Math.cos(2 * spiralAngle - 0.52), 5.1);
          const ridgeNoise = Math.abs(fbm5(dx * 15.0 + 2.5, dy * 15.0 + 8.1) - 0.48);
          const dustFilament = Math.max(0, 1.0 - ridgeNoise * 6.5);
          const dustStrength =
            (dustShock * 0.78 + dustFilament * 0.55) *
            Math.exp(-Math.pow((r - 0.34) / 0.31, 2));
          const transmittance = Math.max(0.06, 1.0 - dustStrength * 0.93);

          const armLum =
            diskEnvelope *
            (0.12 + 0.98 * armSignal * (0.42 + 0.88 * gasTurb) * (0.62 + 0.58 * fineDetail));
          const totalLum = (bulge + armLum) * transmittance;

          if (totalLum < 0.0035) continue;

          const blueBoost = styleKey === "spiral-blue-hii" ? 1.15 : 1.0;
          const blueFactor = Math.min(1, Math.max(0, (r - 0.12) * 1.9 * blueBoost)) * armSignal;
          const warmFactor = 1.0 - blueFactor * 0.82;
          const hiiKnot =
            armSignal > 0.6 && fineDetail > 0.71 && r > 0.15 ? (fineDetail - 0.71) * 4.0 : 0;

          const rRaw = totalLum * (255 * warmFactor + 125 * blueFactor) + hiiKnot * 175;
          const gRaw = totalLum * (210 * warmFactor + 204 * blueFactor) + hiiKnot * 44;
          const bRaw = totalLum * (152 * warmFactor + 250 * blueFactor) + hiiKnot * 82;

          const tint = GALAXY_PALETTES[styleKey] || [1, 1, 1];
          red = 255 * (1 - Math.exp(-(rRaw * tint[0]) / 150));
          green = 255 * (1 - Math.exp(-(gRaw * tint[1]) / 155));
          blue = 255 * (1 - Math.exp(-(bRaw * tint[2]) / 160));
          alpha = Math.min(255, 255 * (1 - Math.exp(-totalLum * 2.75)));
        }

        const idx = (py * size + px) * 4;
        data[idx] = red;
        data[idx + 1] = green;
        data[idx + 2] = blue;
        data[idx + 3] = alpha;
      }
    }

    ctx.putImageData(imgData, 0, 0);

    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    const isElliptical = styleKey.startsWith("elliptical");
    const nSprinkle = Math.round((isElliptical ? 900 : 3400) * (size / 900) ** 2);
    for (let s = 0; s < nSprinkle; s++) {
      if (isElliptical) break;                    // une elliptique n'a pas de bras d'étoiles
      const armIdx = s % 2;
      const rNorm = Math.pow(seededRand(s + 40000), 0.85);
      const r = (0.03 + rNorm * 0.9) * half;
      const spread = (seededRand(s + 41000) - 0.5) * (0.36 + rNorm * 0.58);
      const theta = armIdx * Math.PI - 3.65 * Math.log(rNorm + 0.05) + spread;
      const sx = half + Math.cos(theta) * r;
      const sy = half + Math.sin(theta) * r;
      const sr = 0.32 + seededRand(s + 42000) * 0.92;
      const sa = (1 - rNorm * 0.62) * (0.22 + seededRand(s + 43000) * 0.72);
      const starCol =
        rNorm < 0.24 ? "255, 224, 178" : s % 3 === 0 ? "170, 220, 248" : "237, 240, 247";

      ctx.fillStyle = `rgba(${starCol}, ${sa.toFixed(3)})`;
      ctx.beginPath();
      ctx.arc(sx, sy, sr, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    return canvas;
  }

  ["spiral-gold-blue", "spiral-blue-hii", "sombrero-dust-ring", "magellanic-irregular"].forEach(
    (key) => {
      galaxyTextures[key] = createGalaxyTexture(key);
    }
  );
  // textures plus légères pour les galaxies de décor
  ["spiral-violet", "spiral-rose", "spiral-ice", "elliptical-warm", "elliptical-ice"].forEach((key) => {
    galaxyTextures[key] = createGalaxyTexture(key, 440);
  });

  // =========================================================
  // 6b. Galaxies de décor (sans nom) : l'univers paraît plein
  // =========================================================
  const SCENERY_STYLES = [
    "spiral-violet", "elliptical-warm", "spiral-rose", "spiral-blue-hii", "spiral-ice",
    "elliptical-ice", "spiral-gold-blue", "magellanic-irregular", "sombrero-dust-ring",
  ];

  const SCENERY_GALAXIES = (() => {
    const out = [];
    const taken = SPHEREX_GALAXIES.map((g) => ({ ...g.pos3D, r: g.radius3D }));
    for (let i = 0, tries = 0; out.length < 16 && tries < 600; tries++) {
      const a = seededRand(tries * 7 + 501) * Math.PI * 2;
      const d = 560 + seededRand(tries * 7 + 502) * 560;
      const pos = {
        x: Math.cos(a) * d,
        y: Math.sin(a) * d * 0.85,
        z: (seededRand(tries * 7 + 503) - 0.5) * 520,
      };
      const radius = 48 + seededRand(tries * 7 + 504) * 82;
      // pas de chevauchement avec les autres galaxies
      const clash = taken.some((t) => Math.hypot(t.x - pos.x, t.y - pos.y, t.z - pos.z) < (t.r + radius) * 0.95);
      if (clash) continue;
      taken.push({ ...pos, r: radius });
      const edgeOn = seededRand(tries * 7 + 505) < 0.22;   // quelques-unes vues par la tranche
      out.push({
        id: `decor-${i}`,
        decor: true,
        style: SCENERY_STYLES[i % SCENERY_STYLES.length],
        pos3D: pos,
        radius3D: radius,
        tiltX: edgeOn ? 1.38 + seededRand(tries * 7 + 506) * 0.12 : (seededRand(tries * 7 + 506) - 0.5) * 1.8,
        tiltY: (seededRand(tries * 7 + 507) - 0.5) * 1.6,
        spinSpeed: (seededRand(tries * 7 + 508) < 0.5 ? -1 : 1) * (0.025 + seededRand(tries * 7 + 509) * 0.04),
      });
      i++;
    }
    return out;
  })();

  // champ profond : petites galaxies très lointaines (taches floues de couleurs variées)
  function makeSmudge(rgb, flat) {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const x = c.getContext("2d");
    x.translate(32, 32);
    x.scale(1, flat);
    const g = x.createRadialGradient(0, 0, 0, 0, 0, 30);
    g.addColorStop(0, `rgba(${rgb}, 1)`);
    g.addColorStop(0.18, `rgba(${rgb}, 0.65)`);
    g.addColorStop(0.55, `rgba(${rgb}, 0.16)`);
    g.addColorStop(1, `rgba(${rgb}, 0)`);
    x.fillStyle = g;
    x.beginPath();
    x.arc(0, 0, 30, 0, Math.PI * 2);
    x.fill();
    return c;
  }
  const SMUDGES = [
    makeSmudge("255, 222, 170", 1), makeSmudge("255, 222, 170", 0.55), makeSmudge("190, 210, 255", 0.4),
    makeSmudge("220, 180, 255", 0.6), makeSmudge("255, 190, 205", 0.75), makeSmudge("200, 235, 255", 0.3),
  ];
  const deepGalaxies3D = Array.from({ length: 140 }, (_, i) => {
    const u = seededRand(i + 7100), v = seededRand(i + 7200);
    const theta = u * 2 * Math.PI, phi = Math.acos(2 * v - 1);
    const r = 900 + seededRand(i + 7300) * 700;
    return {
      x: r * Math.sin(phi) * Math.cos(theta),
      y: r * Math.sin(phi) * Math.sin(theta),
      z: r * Math.cos(phi),
      size: 3 + seededRand(i + 7400) ** 2 * 11,
      rot: seededRand(i + 7500) * Math.PI,
      alpha: 0.25 + seededRand(i + 7600) * 0.55,
      sprite: SMUDGES[i % SMUDGES.length],
    };
  });

  // =========================================================
  // 7. True 3D Universe Camera, Controls & Perspective Engine
  // =========================================================
  let stageW = 0;
  let stageH = 0;
  let deepStars3D = [];
  let diffractionStars = [];
  let galaxySpinTime = 0;
  let autoOrbitEnabled = true;

  const cam3D = {
    focusX: 0,
    focusY: 0,
    focusZ: 0,
    yaw: 0.25,
    pitch: 1.04,
    zoom: 1.15,
    panX: 0,
    panY: 0,
    dim: 0,
  };

  const ZOOM_DURATION_MS = 2150;
  let camFlight = {
    active: false,
    startTime: 0,
    duration: ZOOM_DURATION_MS,
    from: { ...cam3D },
    to: { ...cam3D },
  };

  function flyCamera3D(goal, opts = {}) {
    const targetState = {
      focusX: goal.focusX ?? cam3D.focusX,
      focusY: goal.focusY ?? cam3D.focusY,
      focusZ: goal.focusZ ?? cam3D.focusZ,
      yaw: goal.yaw ?? cam3D.yaw,
      pitch: goal.pitch ?? cam3D.pitch,
      zoom: goal.zoom ?? cam3D.zoom,
      panX: goal.panX ?? 0,
      panY: goal.panY ?? 0,
      dim: goal.dim ?? cam3D.dim,
    };

    if (prefersReducedMotion) {
      Object.assign(cam3D, targetState);
      camFlight.active = false;
      syncCamControlsUI();
      return;
    }

    if (camFlight.intro && !opts.intro) endIntro(false);   // l'utilisateur a pris la main
    camFlight = {
      active: true,
      startTime: performance.now(),
      duration: opts.duration || ZOOM_DURATION_MS,
      ease: opts.ease || null,
      logZoom: !!opts.logZoom,
      intro: !!opts.intro,
      from: { ...cam3D },
      to: targetState,
    };
  }

  // =========================================================
  // 7b. Animation d'ouverture : on arrive de très loin dans l'espace
  // =========================================================
  const INTRO_DURATION_MS = 5200;
  const introOverlay = document.getElementById("intro-overlay");
  const introSkipBtn = document.getElementById("intro-skip");
  let introRunning = false;

  // lent au départ, rapide au milieu, freinage doux à l'arrivée
  const easeInOutQuint = (t) => (t < 0.5 ? 16 * t ** 5 : 1 - (-2 * t + 2) ** 5 / 2);

  function introProgress(now) {
    if (!introRunning || !camFlight.intro) return 1;
    return Math.min(1, Math.max(0, (now - camFlight.startTime) / camFlight.duration));
  }

  function startIntro() {
    const home = { ...cam3D };
    if (prefersReducedMotion) return;
    introRunning = true;
    document.body.classList.add("intro-running");
    introOverlay?.classList.remove("is-hidden");
    // point de départ : très très loin, vu presque par la tranche, tourné
    Object.assign(cam3D, { zoom: 0.018, yaw: home.yaw - 2.6, pitch: 0.32, panX: 0, panY: 0, dim: 0 });
    flyCamera3D(home, { duration: INTRO_DURATION_MS, ease: easeInOutQuint, logZoom: true, intro: true });
  }

  function endIntro(jumpToEnd) {
    if (!introRunning) return;
    introRunning = false;
    if (jumpToEnd && camFlight.intro) {
      Object.assign(cam3D, camFlight.to);
      camFlight.active = false;
    }
    camFlight.intro = false;
    document.body.classList.remove("intro-running");
    document.body.classList.add("intro-reveal");          // les panneaux apparaissent un à un
    setTimeout(() => document.body.classList.remove("intro-reveal"), 2200);
    introOverlay?.classList.add("is-fading");
    setTimeout(() => {
      introOverlay?.classList.add("is-hidden");
      introOverlay?.classList.remove("is-fading");
    }, 900);
    syncCamControlsUI();
  }

  // toucher la vue pendant l'approche = passer l'introduction
  ["mousedown", "wheel", "touchstart"].forEach((ev) =>
    skyCanvas?.addEventListener(ev, () => { if (introRunning) endIntro(true); }, { passive: true }));

  introSkipBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    endIntro(true);
  });
  window.addEventListener("keydown", (e) => {
    if (introRunning && (e.key === "Escape" || e.key === " " || e.key === "Enter")) endIntro(true);
  });

  // traînées d'étoiles « vitesse lumière » pendant l'approche
  const WARP_STREAKS = Array.from({ length: 220 }, (_, i) => ({
    a: seededRand(i + 9100) * Math.PI * 2,
    phase: seededRand(i + 9200),
    speed: 0.6 + seededRand(i + 9300) * 0.9,
    width: 0.6 + seededRand(i + 9400) * 1.4,
    tint: i % 5 === 0 ? "170, 220, 255" : i % 7 === 0 ? "255, 214, 170" : "237, 240, 247",
  }));

  function drawWarp(now, t) {
    // intensité : monte vite, culmine au milieu du voyage, s'éteint avant l'arrivée
    const k = Math.max(0, Math.sin(Math.PI * Math.min(1, t / 0.82)));
    if (k < 0.01) return;
    const cx = stageW * 0.5, cy = stageH * 0.5;
    const R = Math.hypot(stageW, stageH) * 0.55;
    const tt = now / 1000;
    skyCtx.save();
    skyCtx.globalCompositeOperation = "lighter";
    skyCtx.lineCap = "round";
    for (const st of WARP_STREAKS) {
      const f = (st.phase + tt * st.speed * (0.35 + 1.6 * k)) % 1;
      const r1 = R * f * f;
      const len = R * (0.02 + 0.22 * k) * (0.3 + f);
      const r0 = Math.max(0, r1 - len);
      const ca = Math.cos(st.a), sa = Math.sin(st.a);
      const g = skyCtx.createLinearGradient(cx + ca * r0, cy + sa * r0, cx + ca * r1, cy + sa * r1);
      g.addColorStop(0, `rgba(${st.tint}, 0)`);
      g.addColorStop(1, `rgba(${st.tint}, ${(0.85 * k * Math.min(1, f * 3)).toFixed(3)})`);
      skyCtx.strokeStyle = g;
      skyCtx.lineWidth = st.width * (0.6 + f);
      skyCtx.beginPath();
      skyCtx.moveTo(cx + ca * r0, cy + sa * r0);
      skyCtx.lineTo(cx + ca * r1, cy + sa * r1);
      skyCtx.stroke();
    }
    // lueur au centre : l'univers local qui approche
    const glow = skyCtx.createRadialGradient(cx, cy, 0, cx, cy, R * 0.35);
    glow.addColorStop(0, `rgba(120, 200, 255, ${(0.18 * k).toFixed(3)})`);
    glow.addColorStop(1, "rgba(120, 200, 255, 0)");
    skyCtx.fillStyle = glow;
    skyCtx.fillRect(0, 0, stageW, stageH);
    skyCtx.restore();
  }

  function project3D(wx, wy, wz) {
    const dx = wx - cam3D.focusX;
    const dy = wy - cam3D.focusY;
    const dz = wz - cam3D.focusZ;

    const cosY = Math.cos(cam3D.yaw);
    const sinY = Math.sin(cam3D.yaw);
    const rx = dx * cosY - dy * sinY;
    const ry = dx * sinY + dy * cosY;
    const rz = dz;

    const cosP = Math.cos(cam3D.pitch);
    const sinP = Math.sin(cam3D.pitch);
    const camSpaceY = ry * cosP - rz * sinP;
    const camSpaceDepth = ry * sinP + rz * cosP;

    const fovDist = 1150;
    const persp = fovDist / Math.max(240, fovDist + camSpaceDepth);
    const scale = cam3D.zoom * persp;

    return {
      x: stageW * 0.5 + cam3D.panX + rx * scale,
      y: stageH * 0.5 + cam3D.panY + camSpaceY * scale,
      depth: camSpaceDepth,
      scale,
    };
  }

  function build3DStarfield() {
    const rect = galaxyStage.getBoundingClientRect();
    stageW = Math.max(300, Math.round(rect.width));
    stageH = Math.max(300, Math.round(rect.height));

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    skyCanvas.width = Math.round(stageW * dpr);
    skyCanvas.height = Math.round(stageH * dpr);
    skyCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

    deepStars3D = Array.from({ length: 320 }, (_, i) => {
      const u = seededRand(i + 10);
      const v = seededRand(i + 20);
      const theta = u * 2 * Math.PI;
      const phi = Math.acos(2 * v - 1);
      const r = 750 + seededRand(i + 30) * 650;
      return {
        x: r * Math.sin(phi) * Math.cos(theta),
        y: r * Math.sin(phi) * Math.sin(theta),
        z: r * Math.cos(phi),
        size: 0.45 + seededRand(i + 40) * 1.25,
        alpha: 0.24 + seededRand(i + 50) * 0.65,
        tint: i % 4 === 0 ? "178, 218, 232" : i % 7 === 0 ? "242, 204, 162" : "237, 240, 247",
      };
    });

    diffractionStars = Array.from({ length: 9 }, (_, i) => ({
      x: (0.07 + seededRand(i + 800) * 0.86) * stageW,
      y: (0.07 + seededRand(i + 900) * 0.86) * stageH,
      spikeLen: 9 + seededRand(i + 1000) * 11,
      tint: i % 2 === 0 ? "215, 236, 250" : "250, 224, 190",
    }));
  }

  let isStageDragging = false;
  let stageDragMode = "rotate";
  let lastStageMouse = { x: 0, y: 0 };
  let stageDragMoved = false;

  function syncCamControlsUI() {
    camZoomReadout.textContent = `${cam3D.zoom.toFixed(2)}x`;
    camZoomSlider.value = String(Math.min(4.5, Math.max(0.45, cam3D.zoom)));

    camPresetTop.classList.toggle("active", cam3D.pitch < 0.25);
    camPresetEdge.classList.toggle("active", cam3D.pitch > 1.38);
    camPreset3d.classList.toggle("active", cam3D.pitch >= 0.25 && cam3D.pitch <= 1.38);
    camAutorotateBtn.classList.toggle("active", autoOrbitEnabled);
  }

  camPreset3d.addEventListener("click", () => flyCamera3D({ pitch: 1.04 }));
  camPresetTop.addEventListener("click", () => flyCamera3D({ pitch: 0.04 }));
  camPresetEdge.addEventListener("click", () => flyCamera3D({ pitch: 1.51 }));

  camAutorotateBtn.addEventListener("click", () => {
    autoOrbitEnabled = !autoOrbitEnabled;
    syncCamControlsUI();
  });

  camZoomInBtn.addEventListener("click", () => {
    camFlight.active = false;
    cam3D.zoom = Math.min(4.5, cam3D.zoom * 1.25);
    syncCamControlsUI();
  });

  camZoomOutBtn.addEventListener("click", () => {
    camFlight.active = false;
    cam3D.zoom = Math.max(0.45, cam3D.zoom / 1.25);
    syncCamControlsUI();
  });

  camZoomSlider.addEventListener("input", (e) => {
    camFlight.active = false;
    cam3D.zoom = Number.parseFloat(e.target.value) || 1.0;
    camZoomReadout.textContent = `${cam3D.zoom.toFixed(2)}x`;
  });

  camResetBtn.addEventListener("click", () => {
    if (selectedTarget) {
      returnToGalaxyView(true);
    } else {
      setActiveGalaxy(activeGalaxyId);
    }
  });

  skyCanvas.addEventListener("mousedown", (e) => {
    isStageDragging = true;
    stageDragMoved = false;
    stageDragMode = e.shiftKey || e.button === 2 ? "pan" : "rotate";
    lastStageMouse = { x: e.clientX, y: e.clientY };
  });

  skyCanvas.addEventListener("contextmenu", (e) => e.preventDefault());

  window.addEventListener("mousemove", (e) => {
    if (!isStageDragging) return;
    const dx = e.clientX - lastStageMouse.x;
    const dy = e.clientY - lastStageMouse.y;
    if (Math.hypot(dx, dy) > 3) stageDragMoved = true;
    lastStageMouse = { x: e.clientX, y: e.clientY };

    camFlight.active = false;
    if (stageDragMode === "pan") {
      cam3D.panX += dx;
      cam3D.panY += dy;
    } else {
      cam3D.yaw += dx * 0.0065;
      cam3D.pitch = Math.min(1.54, Math.max(0.02, cam3D.pitch + dy * 0.0065));
      syncCamControlsUI();
    }
  });

  window.addEventListener("mouseup", () => {
    isStageDragging = false;
  });

  skyCanvas.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      camFlight.active = false;
      const factor = e.deltaY < 0 ? 1.12 : 0.89;
      cam3D.zoom = Math.min(4.5, Math.max(0.45, cam3D.zoom * factor));
      syncCamControlsUI();
    },
    { passive: false }
  );

  // =========================================================
  // 8. 3D Trajectory Overlay Builder & Live Screen Sync
  // =========================================================
  const TRAJ_START_DELAY_MS = Math.round(ZOOM_DURATION_MS * 0.38);
  const TRAJ_DRAW_DURATION_MS = 1000;
  let trajAnim = {
    active: false,
    startTime: 0,
    progress: 1,
    pts3D: null,
    elements: null,
  };

  function clearTrajectoryOverlay() {
    trajCameraGroup.innerHTML = "";
    trajAnim = { active: false, startTime: 0, progress: 1, pts3D: null, elements: null };
  }

  function buildTrajectoryOverlay3D(target) {
    clearTrajectoryOverlay();
    if (!target) return;

    const enc = getEncodingForTarget(target);
    const w3d = getTargetWorld3D(target);
    // Mouvement MESURÉ par SPHEREx (backend), s'il est connu ; sinon valeurs du catalogue.
    // Position saisie à la main : pas de flèche tant que rien n'est mesuré (pas de valeur inventée).
    const meas = target._measured || null;
    const showArrow = meas ? meas.moving : target.id !== "custom-field";
    let v = target.velVec3D || { x: 0.7, y: -0.5, z: 0.4 };
    let span = target.trajSpan3D || 50;
    if (meas && meas.moving) {
      const pa = ((meas.pa ?? 0) * Math.PI) / 180;      // 0 = nord, 90 = est
      v = { x: -Math.sin(pa), y: -Math.cos(pa), z: 0.15 }; // nord en haut, est à gauche
      span = 25 + 18 * Math.log10(1 + meas.mu);
    }
    const vLen = Math.hypot(v.x, v.y, v.z) || 1;
    const ux = v.x / vLen;
    const uy = v.y / vLen;
    const uz = v.z / vLen;

    const pts3D = {
      start: { x: w3d.x - ux * span, y: w3d.y - uy * span, z: w3d.z - uz * span },
      current: { x: w3d.x, y: w3d.y, z: w3d.z },
      yearProj: {
        x: w3d.x + ux * (span * 1.12),
        y: w3d.y + uy * (span * 1.12),
        z: w3d.z + uz * (span * 1.12),
      },
    };

    const ns = "http://www.w3.org/2000/svg";
    const defs = document.createElementNS(ns, "defs");
    const marker = document.createElementNS(ns, "marker");
    marker.setAttribute("id", "traj-arrowhead-3d");
    marker.setAttribute("markerWidth", "7");
    marker.setAttribute("markerHeight", "7");
    marker.setAttribute("refX", "5");
    marker.setAttribute("refY", "3.5");
    marker.setAttribute("orient", "auto");
    const poly = document.createElementNS(ns, "polygon");
    poly.setAttribute("points", "0 0, 7 3.5, 0 7");
    poly.setAttribute("fill", enc.hex);
    marker.appendChild(poly);
    defs.appendChild(marker);
    trajCameraGroup.appendChild(defs);

    const guidePath = document.createElementNS(ns, "path");
    guidePath.setAttribute("fill", "none");
    guidePath.setAttribute("stroke", `rgba(${enc.rgb}, 0.25)`);
    guidePath.setAttribute("stroke-width", "1.3");
    guidePath.setAttribute("stroke-dasharray", "3 4");
    trajCameraGroup.appendChild(guidePath);

    const activePath = document.createElementNS(ns, "path");
    activePath.setAttribute("fill", "none");
    activePath.setAttribute("stroke", enc.hex);
    activePath.setAttribute("stroke-width", "2.2");
    activePath.setAttribute("stroke-linecap", "round");
    activePath.setAttribute("marker-end", "url(#traj-arrowhead-3d)");
    trajCameraGroup.appendChild(activePath);

    const hitPath = document.createElementNS(ns, "path");
    hitPath.setAttribute("fill", "none");
    hitPath.setAttribute("stroke", "transparent");
    hitPath.setAttribute("stroke-width", "26");
    hitPath.classList.add("svg-anim-trigger");
    hitPath.addEventListener("click", (e) => {
      e.stopPropagation();
      openVideoModal(target);
    });
    trajCameraGroup.appendChild(hitPath);

    const traveler = document.createElementNS(ns, "circle");
    traveler.setAttribute("r", "5");
    traveler.setAttribute("fill", "#edf0f7");
    traveler.setAttribute("stroke", enc.hex);
    traveler.setAttribute("stroke-width", "2");
    traveler.classList.add("svg-anim-trigger");
    traveler.addEventListener("click", (e) => {
      e.stopPropagation();
      openVideoModal(target);
    });
    trajCameraGroup.appendChild(traveler);

    const makeCallout = (title, subtitle, clickable) => {
      const g = document.createElementNS(ns, "g");
      if (clickable) {
        g.classList.add("svg-anim-trigger");
        g.addEventListener("click", (e) => {
          e.stopPropagation();
          openVideoModal(target);
        });
      }

      const tick = document.createElementNS(ns, "line");
      tick.setAttribute("stroke", `rgba(${enc.rgb}, 0.65)`);
      tick.setAttribute("stroke-width", "1");
      g.appendChild(tick);

      const dot = document.createElementNS(ns, "circle");
      dot.setAttribute("r", "3");
      dot.setAttribute("fill", enc.hex);
      g.appendChild(dot);

      const boxW = Math.max(title.length, subtitle.length) * 6.2 + 16;
      const boxH = 28;
      const bg = document.createElementNS(ns, "rect");
      bg.setAttribute("width", boxW.toFixed(0));
      bg.setAttribute("height", boxH);
      bg.setAttribute("rx", "5");
      bg.setAttribute("fill", clickable ? "rgba(18, 12, 6, 0.95)" : "rgba(2, 3, 7, 0.92)");
      bg.setAttribute("stroke", clickable ? enc.hex : `rgba(${enc.rgb}, 0.45)`);
      bg.setAttribute("stroke-width", clickable ? "1.1" : "0.8");
      g.appendChild(bg);

      const t1 = document.createElementNS(ns, "text");
      t1.setAttribute("fill", "#edf0f7");
      t1.setAttribute("font-family", "ui-monospace, SFMono-Regular, Menlo, monospace");
      t1.setAttribute("font-size", "9.5px");
      t1.setAttribute("font-weight", "700");
      t1.textContent = title;
      g.appendChild(t1);

      const t2 = document.createElementNS(ns, "text");
      t2.setAttribute("fill", enc.hex);
      t2.setAttribute("font-family", "ui-monospace, SFMono-Regular, Menlo, monospace");
      t2.setAttribute("font-size", "8.6px");
      t2.textContent = subtitle;
      g.appendChild(t2);

      trajCameraGroup.appendChild(g);
      return { g, tick, dot, bg, t1, t2, boxW, boxH };
    };

    const fmtMu = (x) => (x == null ? "?" : x.toFixed(x < 1 ? 2 : 1));
    const callouts = meas
      ? {
          start: makeCallout("1re image SPHEREx", meas.start || "", false),
          current: makeCallout(meas.moving ? `SPHEREx • ${fmtMu(meas.mu)}″/an` : "SPHEREx",
                               "🎬 Clic : vidéo SPHEREx", true),
          yearProj: makeCallout("Mesuré par SPHEREx",
                                `μ = ${fmtMu(meas.mu)} ± ${fmtMu(meas.err)}″/an`, true),
        }
      : target.id === "custom-field"
        ? {
            start: makeCallout("", "", false),
            current: makeCallout("SPHEREx", "🎬 Clic : vidéo SPHEREx", true),
            yearProj: makeCallout("", "", true),
          }
        : {
            start: makeCallout("EPOCH 1 (3D)", "2025-05-12", false),
            current: makeCallout(`3D • ${target.velocityKms}`, "🎬 Click: Follow-Zoom Pop-up", true),
            yearProj: makeCallout(`+1-YR: ${target.trajPerYearKm}`, `μ = ${target.properMotion}`, true),
          };
    if (!showArrow) {
      // objet immobile ou mouvement non mesuré : pas de flèche ni d'étiquettes de trajectoire
      [guidePath, activePath, hitPath, traveler, callouts.start.g, callouts.yearProj.g]
        .forEach((el) => el && (el.style.display = "none"));
    }

    trajAnim = {
      active: !prefersReducedMotion,
      startTime: performance.now() + TRAJ_START_DELAY_MS,
      progress: prefersReducedMotion ? 1 : 0,
      pts3D,
      elements: { guidePath, activePath, hitPath, traveler, callouts },
    };
  }

  function updateTrajectoryOverlay3D(now) {
    if (!trajAnim.pts3D || !trajAnim.elements) return;

    if (trajAnim.active && now >= trajAnim.startTime) {
      const rawT = (now - trajAnim.startTime) / TRAJ_DRAW_DURATION_MS;
      const clamped = Math.min(1, Math.max(0, rawT));
      trajAnim.progress = cubicBezierEaseOut(clamped);
      if (clamped >= 1) trajAnim.active = false;
    }

    const { pts3D, elements, progress } = trajAnim;
    const p0 = project3D(pts3D.start.x, pts3D.start.y, pts3D.start.z);
    const p1 = project3D(pts3D.current.x, pts3D.current.y, pts3D.current.z);
    const p2 = project3D(pts3D.yearProj.x, pts3D.yearProj.y, pts3D.yearProj.z);

    const fullD = `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)} L ${p1.x.toFixed(1)} ${p1.y.toFixed(1)} L ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    elements.guidePath.setAttribute("d", fullD);
    elements.hitPath.setAttribute("d", fullD);

    let curPt;
    let activeD;
    if (progress <= 0.5) {
      const t = progress * 2;
      curPt = { x: p0.x + (p1.x - p0.x) * t, y: p0.y + (p1.y - p0.y) * t };
      activeD = `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)} L ${curPt.x.toFixed(1)} ${curPt.y.toFixed(1)}`;
    } else {
      const t = (progress - 0.5) * 2;
      curPt = { x: p1.x + (p2.x - p1.x) * t, y: p1.y + (p2.y - p1.y) * t };
      activeD = `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)} L ${p1.x.toFixed(1)} ${p1.y.toFixed(1)} L ${curPt.x.toFixed(1)} ${curPt.y.toFixed(1)}`;
    }

    elements.activePath.setAttribute("d", activeD);
    elements.traveler.setAttribute("cx", curPt.x.toFixed(1));
    elements.traveler.setAttribute("cy", curPt.y.toFixed(1));

    const positionCallout = (cObj, pt, sideX, sideY) => {
      const lx = pt.x + sideX;
      const ly = pt.y + sideY;
      cObj.dot.setAttribute("cx", pt.x.toFixed(1));
      cObj.dot.setAttribute("cy", pt.y.toFixed(1));
      cObj.tick.setAttribute("x1", pt.x.toFixed(1));
      cObj.tick.setAttribute("y1", pt.y.toFixed(1));
      cObj.tick.setAttribute("x2", lx.toFixed(1));
      cObj.tick.setAttribute("y2", ly.toFixed(1));

      const alignRight = sideX >= 0;
      const boxX = alignRight ? lx + 4 : lx - cObj.boxW - 4;
      const boxY = ly - cObj.boxH * 0.5;
      cObj.bg.setAttribute("x", boxX.toFixed(1));
      cObj.bg.setAttribute("y", boxY.toFixed(1));
      cObj.t1.setAttribute("x", (boxX + 8).toFixed(1));
      cObj.t1.setAttribute("y", (boxY + 12).toFixed(1));
      cObj.t2.setAttribute("x", (boxX + 8).toFixed(1));
      cObj.t2.setAttribute("y", (boxY + 23).toFixed(1));
      cObj.g.style.opacity = progress > 0.35 ? "1" : "0";
    };

    positionCallout(elements.callouts.start, p0, -24, -24);
    positionCallout(elements.callouts.current, p1, 22, 24);
    positionCallout(elements.callouts.yearProj, p2, 22, -22);
  }

  // =========================================================
  // 9. True 3D Multi-Galaxy Disk & Dwarf Render Loop (60fps)
  // =========================================================
  const sessionStartTime = performance.now();
  let targetLockStartTime = 0;

  function drawGalaxyDisk3D(gal, spinAngle, alphaMultiplier) {
    const tex = galaxyTextures[gal.style] || galaxyTextures["spiral-gold-blue"];
    const R = gal.radius3D;

    const cx = Math.cos(gal.tiltX), sx = Math.sin(gal.tiltX);
    const cy = Math.cos(gal.tiltY), sy = Math.sin(gal.tiltY);

    const rotPoint = (lx, ly) => {
      const y1 = ly * cx;
      const z1 = ly * sx;
      const x2 = lx * cy + z1 * sy;
      const z2 = -lx * sy + z1 * cy;
      return { x: gal.pos3D.x + x2, y: gal.pos3D.y + y1, z: gal.pos3D.z + z2 };
    };

    const pCenter = project3D(gal.pos3D.x, gal.pos3D.y, gal.pos3D.z);
    const uWorld = rotPoint(Math.cos(spinAngle) * R, Math.sin(spinAngle) * R);
    const vWorld = rotPoint(-Math.sin(spinAngle) * R, Math.cos(spinAngle) * R);

    const pU = project3D(uWorld.x, uWorld.y, uWorld.z);
    const pV = project3D(vWorld.x, vWorld.y, vWorld.z);

    const ux = pU.x - pCenter.x;
    const uy = pU.y - pCenter.y;
    const vx = pV.x - pCenter.x;
    const vy = pV.y - pCenter.y;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const halfTex = tex.width * 0.5;

    skyCtx.save();
    skyCtx.transform(
      ux / halfTex,
      uy / halfTex,
      vx / halfTex,
      vy / halfTex,
      pCenter.x,
      pCenter.y
    );
    skyCtx.globalAlpha = alphaMultiplier;
    skyCtx.drawImage(tex, -halfTex, -halfTex);
    skyCtx.restore();

    skyCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // pas de nom de galaxie dans la vue 3D : l'univers en général
  }

  function renderFrame(now) {
    const utcIso = new Date().toISOString().replace("T", " ").slice(0, 19);
    liveUtcClock.textContent = `${utcIso} UTC`;

    const sessionElapsedSec = (now - sessionStartTime) / 1000;
    const totalDriftKm = Math.round(sessionElapsedSec * 384.5);
    liveRealtimeDrift.textContent = `Live Session Drift: +${totalDriftKm.toLocaleString()} km`;

    if (selectedTarget && targetLockStartTime > 0) {
      const lockSec = (now - targetLockStartTime) / 1000;
      const traveledKm = (selectedTarget.velocityNum || 0) * lockSec;
      detLiveKm.textContent = `${traveledKm.toLocaleString("en-US", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      })} km`;
    }

    if (camFlight.active) {
      const rawT = (now - camFlight.startTime) / camFlight.duration;
      if (rawT >= 1) {
        Object.assign(cam3D, camFlight.to);
        camFlight.active = false;
        if (camFlight.intro) endIntro(false);
      } else {
        const e = (camFlight.ease || cubicBezierEaseOut)(Math.max(0, rawT));
        cam3D.focusX = camFlight.from.focusX + (camFlight.to.focusX - camFlight.from.focusX) * e;
        cam3D.focusY = camFlight.from.focusY + (camFlight.to.focusY - camFlight.from.focusY) * e;
        cam3D.focusZ = camFlight.from.focusZ + (camFlight.to.focusZ - camFlight.from.focusZ) * e;
        cam3D.yaw = camFlight.from.yaw + (camFlight.to.yaw - camFlight.from.yaw) * e;
        cam3D.pitch = camFlight.from.pitch + (camFlight.to.pitch - camFlight.from.pitch) * e;
        cam3D.zoom = camFlight.logZoom
          ? camFlight.from.zoom * Math.pow(camFlight.to.zoom / camFlight.from.zoom, e)   // zoom régulier
          : camFlight.from.zoom + (camFlight.to.zoom - camFlight.from.zoom) * e;
        cam3D.panX = camFlight.from.panX + (camFlight.to.panX - camFlight.from.panX) * e;
        cam3D.panY = camFlight.from.panY + (camFlight.to.panY - camFlight.from.panY) * e;
        cam3D.dim = camFlight.from.dim + (camFlight.to.dim - camFlight.from.dim) * e;
      }
      syncCamControlsUI();
    } else if (autoOrbitEnabled && !isStageDragging && !prefersReducedMotion) {
      cam3D.yaw += 0.00055;
    }

    if (!prefersReducedMotion) {
      galaxySpinTime += 0.004;
    }

    // la vue a changé de taille (barre de gauche qui se replie / glisse) : canvas ajusté
    const stageRect = galaxyStage.getBoundingClientRect();
    if (Math.max(300, Math.round(stageRect.width)) !== stageW ||
        Math.max(300, Math.round(stageRect.height)) !== stageH) {
      build3DStarfield();
    }

    skyCtx.fillStyle = "#000001";
    skyCtx.fillRect(0, 0, stageW, stageH);

    for (const st of deepStars3D) {
      const p = project3D(st.x + cam3D.focusX * 0.25, st.y + cam3D.focusY * 0.25, st.z + cam3D.focusZ * 0.25);
      if (p.x < -10 || p.x > stageW + 10 || p.y < -10 || p.y > stageH + 10) continue;
      skyCtx.fillStyle = `rgba(${st.tint}, ${st.alpha})`;
      skyCtx.beginPath();
      skyCtx.arc(p.x, p.y, st.size, 0, Math.PI * 2);
      skyCtx.fill();
    }

    // petites galaxies lointaines (parallaxe comme les étoiles de fond)
    skyCtx.save();
    skyCtx.globalCompositeOperation = "lighter";
    for (const dg of deepGalaxies3D) {
      const p = project3D(dg.x + cam3D.focusX * 0.25, dg.y + cam3D.focusY * 0.25, dg.z + cam3D.focusZ * 0.25);
      const sz = dg.size * Math.min(1.6, Math.max(0.5, p.scale * 1.4));
      if (p.x < -sz || p.x > stageW + sz || p.y < -sz || p.y > stageH + sz) continue;
      skyCtx.globalAlpha = dg.alpha * (1 - cam3D.dim * 0.4);
      skyCtx.translate(p.x, p.y);
      skyCtx.rotate(dg.rot + cam3D.yaw * 0.3);
      skyCtx.drawImage(dg.sprite, -sz, -sz, sz * 2, sz * 2);
      skyCtx.setTransform(1, 0, 0, 1, 0, 0);
      const dpr0 = Math.min(window.devicePixelRatio || 1, 2);
      skyCtx.setTransform(dpr0, 0, 0, dpr0, 0, 0);
    }
    skyCtx.restore();

    for (const ds of diffractionStars) {
      const len = ds.spikeLen;
      const gH = skyCtx.createLinearGradient(ds.x - len, ds.y, ds.x + len, ds.y);
      gH.addColorStop(0, `rgba(${ds.tint}, 0)`);
      gH.addColorStop(0.5, `rgba(${ds.tint}, 0.52)`);
      gH.addColorStop(1, `rgba(${ds.tint}, 0)`);
      skyCtx.strokeStyle = gH;
      skyCtx.lineWidth = 0.9;
      skyCtx.beginPath();
      skyCtx.moveTo(ds.x - len, ds.y);
      skyCtx.lineTo(ds.x + len, ds.y);
      skyCtx.stroke();

      const gV = skyCtx.createLinearGradient(ds.x, ds.y - len, ds.x, ds.y + len);
      gV.addColorStop(0, `rgba(${ds.tint}, 0)`);
      gV.addColorStop(0.5, `rgba(${ds.tint}, 0.52)`);
      gV.addColorStop(1, `rgba(${ds.tint}, 0)`);
      skyCtx.strokeStyle = gV;
      skyCtx.beginPath();
      skyCtx.moveTo(ds.x, ds.y - len);
      skyCtx.lineTo(ds.x, ds.y + len);
      skyCtx.stroke();

      skyCtx.fillStyle = `rgba(${ds.tint}, 0.94)`;
      skyCtx.beginPath();
      skyCtx.arc(ds.x, ds.y, 1.35, 0, Math.PI * 2);
      skyCtx.fill();
    }

    const introT = introProgress(now);
    if (introRunning && introT >= 1) endIntro(true);     // filet de sécurité
    if (introT < 1) {
      drawWarp(now, introT);
      // le titre s'efface quand on arrive
      if (introOverlay) introOverlay.style.setProperty("--intro-t", introT.toFixed(3));
    }

    const galaxiesToDraw =
      activeGalaxyId === "all"
        ? [...SPHEREX_GALAXIES, ...SCENERY_GALAXIES]
        : SPHEREX_GALAXIES.filter((g) => g.id === activeGalaxyId);

    galaxiesToDraw.sort((a, b) => {
      const pa = project3D(a.pos3D.x, a.pos3D.y, a.pos3D.z);
      const pb = project3D(b.pos3D.x, b.pos3D.y, b.pos3D.z);
      return pb.depth - pa.depth;
    });

    for (const gal of galaxiesToDraw) {
      const alpha = (gal.decor ? 0.9 : 1) - cam3D.dim * 0.34;
      drawGalaxyDisk3D(gal, galaxySpinTime * gal.spinSpeed, alpha);
    }

    const visibleTargets = getFilteredTargets().map((t) => {
      const w3d = getTargetWorld3D(t);
      const proj = project3D(w3d.x, w3d.y, w3d.z);
      const planeProj = project3D(w3d.x, w3d.y, w3d.planeZ);
      return { target: t, w3d, proj, planeProj };
    });

    visibleTargets.sort((a, b) => b.proj.depth - a.proj.depth);
    // les objets (et leurs étiquettes) n'apparaissent qu'à la fin de l'approche
    skyCtx.globalAlpha = introT < 1 ? Math.max(0, (introT - 0.72) / 0.28) : 1;

    for (const item of visibleTargets) {
      const { target, w3d, proj, planeProj } = item;
      target._screenX = proj.x;
      target._screenY = proj.y;

      const isSelected = selectedTarget?.id === target.id;
      const isHovered = hoveredTarget?.id === target.id;
      const enc = getEncodingForTarget(target);

      const isDimmed = selectedTarget && !isSelected;
      const alphaFactor = isDimmed ? 1 - cam3D.dim * 0.78 : 1;
      const colorRgb = isDimmed && cam3D.dim > 0.35 ? "148, 155, 170" : enc.rgb;

      skyCtx.strokeStyle = `rgba(${colorRgb}, ${(0.35 * alphaFactor).toFixed(3)})`;
      skyCtx.lineWidth = 1;
      skyCtx.setLineDash([2, 2]);
      skyCtx.beginPath();
      skyCtx.moveTo(planeProj.x, planeProj.y);
      skyCtx.lineTo(proj.x, proj.y);
      skyCtx.stroke();
      skyCtx.setLineDash([]);

      skyCtx.fillStyle = `rgba(${colorRgb}, ${(0.45 * alphaFactor).toFixed(3)})`;
      skyCtx.beginPath();
      skyCtx.arc(planeProj.x, planeProj.y, 2, 0, Math.PI * 2);
      skyCtx.fill();

      if (!selectedTarget && target.velVec3D) {
        const vScale = 24;
        const tip3D = project3D(
          w3d.x + target.velVec3D.x * vScale,
          w3d.y + target.velVec3D.y * vScale,
          w3d.z + target.velVec3D.z * vScale
        );
        skyCtx.strokeStyle = `rgba(${colorRgb}, 0.55)`;
        skyCtx.lineWidth = 1.2;
        skyCtx.beginPath();
        skyCtx.moveTo(proj.x, proj.y);
        skyCtx.lineTo(tip3D.x, tip3D.y);
        skyCtx.stroke();
      }

      const markerR = enc.baseRadius * Math.min(1.8, Math.max(0.75, proj.scale * 0.85));
      const haloR = markerR * (isSelected || isHovered ? 3.8 : 2.8);

      const halo = skyCtx.createRadialGradient(proj.x, proj.y, 1, proj.x, proj.y, haloR);
      halo.addColorStop(0, `rgba(${colorRgb}, ${(0.92 * alphaFactor).toFixed(3)})`);
      halo.addColorStop(0.45, `rgba(${colorRgb}, ${(0.26 * alphaFactor).toFixed(3)})`);
      halo.addColorStop(1, `rgba(${colorRgb}, 0)`);
      skyCtx.fillStyle = halo;
      skyCtx.beginPath();
      skyCtx.arc(proj.x, proj.y, haloR, 0, Math.PI * 2);
      skyCtx.fill();

      skyCtx.fillStyle = `rgba(237, 240, 247, ${alphaFactor.toFixed(3)})`;
      skyCtx.beginPath();
      skyCtx.arc(proj.x, proj.y, markerR * 0.55, 0, Math.PI * 2);
      skyCtx.fill();

      skyCtx.strokeStyle = `rgba(${colorRgb}, ${alphaFactor.toFixed(3)})`;
      skyCtx.lineWidth = isSelected ? 2 : 1.4;
      skyCtx.beginPath();
      skyCtx.arc(proj.x, proj.y, markerR, 0, Math.PI * 2);
      skyCtx.stroke();

      if (isSelected || isHovered) {
        skyCtx.strokeStyle = isSelected ? "rgba(56, 178, 172, 0.92)" : "rgba(237, 240, 247, 0.78)";
        skyCtx.lineWidth = 1.4;
        skyCtx.beginPath();
        skyCtx.arc(proj.x, proj.y, markerR + 6, 0, Math.PI * 2);
        skyCtx.stroke();
      }

      const labelText = target.shortName || target.name;
      skyCtx.font = isSelected || isHovered ? "600 11.5px system-ui" : "500 10.5px system-ui";
      const textMetrics = skyCtx.measureText(labelText);
      const pillW = textMetrics.width + 12;
      const pillH = 17;
      const pillX = proj.x - pillW / 2;
      const pillY = proj.y + markerR + 7;

      skyCtx.fillStyle = `rgba(0, 0, 1, ${(0.92 * alphaFactor).toFixed(3)})`;
      skyCtx.beginPath();
      skyCtx.roundRect(pillX, pillY, pillW, pillH, 5);
      skyCtx.fill();

      skyCtx.strokeStyle = isSelected
        ? `rgba(56, 178, 172, ${(0.72 * alphaFactor).toFixed(3)})`
        : `rgba(237, 240, 247, ${(0.16 * alphaFactor).toFixed(3)})`;
      skyCtx.lineWidth = 0.8;
      skyCtx.stroke();

      skyCtx.fillStyle = `rgba(237, 240, 247, ${(0.96 * alphaFactor).toFixed(3)})`;
      skyCtx.textAlign = "center";
      skyCtx.textBaseline = "middle";
      skyCtx.fillText(labelText, proj.x, pillY + pillH / 2 + 0.5);
    }

    skyCtx.globalAlpha = 1;
    updateTrajectoryOverlay3D(now);

    if (isModalOpen && selectedTarget) {
      renderModalSimulation(now);
    }

    requestAnimationFrame(renderFrame);
  }

  // =========================================================
  // 10. Stage Hover & Click Hit-Testing
  // =========================================================
  function findTargetAt(mx, my) {
    const targets = getFilteredTargets();
    let closest = null;
    let minDist = 26;

    for (const t of targets) {
      const dx = mx - (t._screenX || -999);
      const dy = my - (t._screenY || -999);
      const dist = Math.hypot(dx, dy);
      if (dist < minDist) {
        minDist = dist;
        closest = t;
      }
    }
    return closest;
  }

  skyCanvas.addEventListener("mousemove", (e) => {
    if (isStageDragging) {
      tooltip.classList.add("is-hidden");
      return;
    }
    const rect = galaxyStage.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const hit = findTargetAt(mx, my);
    hoveredTarget = hit;

    if (hit) {
      skyCanvas.style.cursor = "pointer";
      tooltipName.textContent = hit.shortName || hit.name;
      tooltipSpec.textContent = hit.spectral || "IR";
      tooltipType.textContent = hit.type;
      tooltipCoords.textContent = `RA ${hit.ra}° • Dec ${hit.dec}°`;
      tooltipMetrics.textContent = `Dist: ${hit.distanceKm} (${hit.distanceLy})`;
      tooltipKinematics.textContent = `3D Velocity: ${hit.velocityKms} • ${hit.trajPerYearKm}`;
      tooltipHint.textContent =
        selectedTarget?.id === hit.id
          ? "Click to open 3D Follow-Zoom Pop-up"
          : "Click to fly in 3D (2.15s) & inspect trajectory";
      tooltip.classList.remove("is-hidden");

      const tipX = Math.min(mx + 14, stageW - 260);
      const tipY = Math.min(my + 14, stageH - 155);
      tooltip.style.left = `${tipX}px`;
      tooltip.style.top = `${tipY}px`;
    } else {
      skyCanvas.style.cursor = "grab";
      tooltip.classList.add("is-hidden");
    }
  });

  skyCanvas.addEventListener("mouseleave", () => {
    hoveredTarget = null;
    tooltip.classList.add("is-hidden");
  });

  skyCanvas.addEventListener("click", (e) => {
    if (stageDragMoved) return;
    const rect = galaxyStage.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const hit = findTargetAt(mx, my);
    if (hit) {
      if (selectedTarget?.id === hit.id) {
        openVideoModal(hit);
      } else {
        selectAndZoomToTarget(hit);
      }
    }
  });

  // =========================================================
  // 11. Select Dwarf, 3D Flight (2.15s), Inspector & Overview
  // =========================================================
  let observationsRequestNo = 0;

  async function selectAndZoomToTarget(target) {
    selectedTarget = target;
    targetLockStartTime = performance.now();
    tooltip.classList.add("is-hidden");
    syncPresetPills(target);

    if (activeGalaxyId !== "all" && activeGalaxyId !== target.galaxyId) {
      activeGalaxyId = target.galaxyId;
      renderGalaxySwitcher();
    }

    raInput.value = target.ra;
    decInput.value = target.dec;
    clearInputErrors();

    try {
      const url = new URL(window.location.href);
      url.searchParams.set("ra", target.ra);
      url.searchParams.set("dec", target.dec);
      url.searchParams.set("fov", fovSelect.value);
      url.searchParams.set("band", detectorSelect.value);
      window.history.replaceState({}, "", url);
    } catch (_) {}

    renderSideList();

    const hostGal = galaxyMap.get(target.galaxyId);
    const w3d = getTargetWorld3D(target);

    inspBadge.textContent = target.type;
    inspFlag.textContent = target.flag || "FLAGS: 0x00 NOMINAL";
    inspTitle.textContent = target.shortName || target.name;
    inspDesignation.textContent = target.name;
    // Paragraphe de présentation : seulement pour les étoiles connues (pas pour une position
    // tapée à la main, ni pour les objets fictifs ou les régions de galaxies)
    const famous = FAMOUS_STARS.has(target.id);
    inspSummary.textContent = famous ? target.summary || target.desc || "" : "";
    inspSummary.classList.toggle("is-hidden", !famous || !inspSummary.textContent);

    detGalaxy.textContent = "";
    detType.textContent = target.type;
    detSpectral.textContent = target.spectral || "Unknown";
    detConstellation.textContent = target.constellation || "Unknown";
    detCoords.textContent = `${target.ra}° (${formatRaHms(target.ra)}) / ${target.dec}° (${formatDecDms(target.dec)})`;
    detXyz3d.textContent = `(${target.local3D.x}, ${target.local3D.y}, ${target.local3D.z >= 0 ? "+" : ""}${target.local3D.z}) ly-eq`;

    detTemp.textContent = target.temp || "Unknown";
    detDistKm.textContent = target.distanceKm || "Unknown";
    detDistLy.textContent = target.distanceLy || "";
    detMass.textContent = target.mass || "Unknown";
    detRadius.textContent = target.radiusKm || "Unknown";
    detAge.textContent = target.age || "Unknown";

    detVelKms.textContent = target.velocityKms || "Unknown";
    detVelKmh.textContent = target.velocityKmh || "";
    detTrajYr.textContent = target.trajPerYearKm || "Unknown";
    detTrajEpoch.textContent = target.trajPerEpochKm || "";
    detLiveKm.textContent = "0.0 km";
    detVelComp.textContent = target.velComponents || "Unknown";
    detPm.textContent = target.properMotion || "Unknown";

    detDiscovery.textContent = target.discovery || "Unknown";
    detFlag.textContent = target.flag || "FLAGS: 0x00 NOMINAL";
    detBandFov.textContent = `${detectorSelect.value} • FOV ${fovSelect.value} arcmin`;
    inspDesc.textContent = target.desc;
    cutoutFovLabel.textContent = `FOV ${fovSelect.value} arcmin • WCS-ICRS`;

    backToGalaxyBtn.classList.remove("is-hidden");
    openAnimModalBtn?.classList.remove("is-hidden");
    inspector.classList.remove("is-closed");
    renderSpectrumPlot(target);

    const detailBiasX = window.innerWidth > 900 ? -135 : 0;
    const detailBiasY = window.innerWidth <= 900 ? -65 : -10;
    flyCamera3D({
      focusX: w3d.x,
      focusY: w3d.y,
      focusZ: w3d.z,
      zoom: 2.65,
      pitch: 1.06,
      panX: detailBiasX,
      panY: detailBiasY,
      dim: 1,
    });

    buildTrajectoryOverlay3D(target);

    const label = target.shortName || target.name;
    const fovArcmin = Number.parseFloat(fovSelect.value) || 10;
    const bandLabel = detectorSelect.value;

    window.dispatchEvent(
      new CustomEvent("spherex:coordinatesChanged", {
        detail: { label, ra: target.ra, dec: target.dec, fov: fovArcmin, band: bandLabel },
      })
    );

    await loadObservations(target);
  }

  // Chargement de la vidéo SPHEREx d'une cible (aussi rappelé quand de nouvelles images
  // SPHEREx ont été intégrées par la mise à jour automatique hebdomadaire)
  async function loadObservations(target) {
    const fovArcmin = Number.parseFloat(fovSelect.value) || 10;
    const bandLabel = detectorSelect.value;
    // Fetch multi-epoch cutouts via F1's single API adapter (observationsApi.js)
    // N° de requête : seule la DERNIÈRE demande peut afficher son résultat
    // (sinon une réponse lente d'une demande précédente remplace la vidéo en cours).
    const requestNo = ++observationsRequestNo;
    try {
      if (typeof window.ObservationsApi?.fetchObservations !== "function") {
        throw new Error("Observation API adapter is not configured.");
      }

      const apiRes = await window.ObservationsApi.fetchObservations({
        ra: target.ra,
        dec: target.dec,
        fov: fovArcmin,
        band: bandLabel,
        target,
      });

      if (requestNo !== observationsRequestNo || selectedTarget?.id !== target.id) return;
      const m = apiRes?.motion;
      target._measured = m
        ? {
            moving: m.status === "moving" && m.mu_arcsec_yr != null,
            mu: m.mu_arcsec_yr,
            err: m.mu_err_arcsec_yr,
            pa: m.position_angle_deg,
            start: m.coverage_start,
          }
        : null;
      buildTrajectoryOverlay3D(target);

      if (!Array.isArray(apiRes?.frames)) {
        throw new Error("Observation API returned an invalid response (expected a frames array).");
      }

      window.dispatchEvent(
        new CustomEvent("spherex:framesLoaded", {
          detail: {
            frames: apiRes.frames,
            video: apiRes.video || null,
            views: apiRes.views || [],
            alert: apiRes.alert || null,
            update: apiRes.update || null,
            resultKey: apiRes.resultKey || null,
            targetId: target.id,
          },
        })
      );
    } catch (err) {
      if (requestNo !== observationsRequestNo || selectedTarget?.id !== target.id) return;
      window.dispatchEvent(
        new CustomEvent("spherex:framesError", {
          detail: { message: err?.message || "Failed to load observations via observationsApi.js." },
        })
      );
    }
  }

  function returnToGalaxyView(triggerFlight = true) {
    try {
      closeVideoModal();
    } catch (_) {}
    closeAnimationModal();
    closeCompareModal();
    selectedTarget = null;
    targetLockStartTime = 0;
    stopPlayback();
    clearTrajectoryOverlay();
    syncPresetPills(null);
    renderSideList();

    if (triggerFlight) {
      if (activeGalaxyId === "all") {
        flyCamera3D({
          focusX: 0,
          focusY: 0,
          focusZ: 0,
          zoom: 0.62,
          pitch: 1.02,
          panX: 0,
          panY: 0,
          dim: 0,
        });
      } else {
        const g = galaxyMap.get(activeGalaxyId) || SPHEREX_GALAXIES[0];
        flyCamera3D({
          focusX: g.pos3D.x,
          focusY: g.pos3D.y,
          focusZ: g.pos3D.z,
          zoom: g.focusZoom || 1.2,
          pitch: 1.04,
          panX: 0,
          panY: 0,
          dim: 0,
        });
      }
    }

    inspector.classList.add("is-closed");
    backToGalaxyBtn.classList.add("is-hidden");
    openAnimModalBtn?.classList.add("is-hidden");

    bodyEl.classList.add("tl-hidden");
    statusEl.className = "timeline-status";
    statusEl.textContent =
      "Drag to rotate the 3D universe, pick an object on the left, or click any object to fly in 3D and inspect its trajectory.";
    statusEl.classList.remove("tl-hidden");
  }

  backToGalaxyBtn.addEventListener("click", () => returnToGalaxyView(true));
  closeInspectorBtn.addEventListener("click", () => returnToGalaxyView(true));

  // =========================================================
  // 12. Pop-up 1: 3D Trajectory Modal with AUTO-FOLLOW Camera Fix
  // =========================================================
  let isModalOpen = false;
  let simPlaying = true;
  let simDirection = 1;
  let simSpeed = 1.0;
  let simElapsedYears = 6.87;
  let lastSimTick = 0;

  let modalFollowDwarf = true;
  let modalZoom = 1.0;
  let modalYaw = 0.36;
  let modalPitch = 1.02;
  let modalCamFocus = { x: 0, y: 0, z: 0 };
  let modalManualPan = { x: 0, y: 0 };

  let isModalDragging = false;
  let modalDragMode = "rotate";
  let lastModalMouse = { x: 0, y: 0 };

  function syncModalHudAndControls() {
    modalZoomSlider.value = String(modalZoom);
    modalZoomReadout.textContent = `${modalZoom.toFixed(1)}x`;
    hudSimZoom.textContent = `${modalZoom.toFixed(1)}x • ${modalFollowDwarf ? "FOLLOW" : "FREE"}`;

    zoomPills.forEach((p) => {
      const z = Number.parseFloat(p.dataset.zoom);
      p.classList.toggle("active", Math.abs(z - modalZoom) < 0.08);
    });

    modalFollowBtn.classList.toggle("is-locked", modalFollowDwarf);
    modalFollowBtn.setAttribute("aria-pressed", String(modalFollowDwarf));
    modalFollowBtn.textContent = modalFollowDwarf
      ? "🎯 Follow Dwarf: ON"
      : "🎯 Follow Dwarf: OFF";
  }

  function setSimSpeed(val) {
    simSpeed = Math.max(0.00000001, val);
    if (simSpeed >= 0.1) {
      modalSpeedSlider.value = String(Math.min(10, simSpeed));
      modalSpeedReadout.textContent = `${simSpeed.toFixed(simSpeed < 1 ? 2 : 1)}x`;
    } else {
      modalSpeedReadout.textContent = "1:1 Real";
    }
    speedPills.forEach((p) => {
      const pVal = Number.parseFloat(p.dataset.speed);
      p.classList.toggle("active", Math.abs(pVal - simSpeed) < 0.01);
    });
  }

  function openAnimationModal(target) {
    if (!target) return;
    isModalOpen = true;
    simPlaying = true;
    simDirection = 1;
    simElapsedYears = 6.87;
    modalFollowDwarf = true;
    modalManualPan = { x: 0, y: 0 };
    modalCamFocus = { x: 0, y: 0, z: 0 };
    lastSimTick = performance.now();

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = modalSimCanvas.getBoundingClientRect();
    const cw = Math.max(320, Math.round(rect.width || 730));
    const ch = Math.max(220, Math.round(rect.height || 325));
    modalSimCanvas.width = Math.round(cw * dpr);
    modalSimCanvas.height = Math.round(ch * dpr);
    modalSimCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const hostGal = galaxyMap.get(target.galaxyId);
    modalGalaxySubtitle.textContent = "3D TRAJECTORY SIMULATOR";
    modalDwarfTitle.textContent = `${target.shortName || target.name} — 3D Follow-Zoom Kinematics`;
    hudSimVel.textContent = target.velocityKms || "Unknown";
    modalPlayBtn.textContent = "⏸ Pause";
    modalDirBtn.textContent = "⇄ Forward";
    modalTimeSlider.value = String(simElapsedYears);

    syncModalHudAndControls();
    animModalBackdrop.classList.remove("is-closed");
  }

  function closeAnimationModal() {
    isModalOpen = false;
    animModalBackdrop.classList.add("is-closed");
  }

  // boutons « 3D Trajectory & Speed » retirés de l'interface (simulateur 3D non utilisé)
  openAnimModalBtn?.addEventListener("click", () => openAnimationModal(selectedTarget));
  inspectorAnimTrigger?.addEventListener("click", () => openAnimationModal(selectedTarget));
  closeAnimModalBtn.addEventListener("click", closeAnimationModal);
  animModalBackdrop.addEventListener("click", (e) => {
    if (e.target === animModalBackdrop) closeAnimationModal();
  });

  modalPlayBtn.addEventListener("click", () => {
    simPlaying = !simPlaying;
    lastSimTick = performance.now();
    modalPlayBtn.textContent = simPlaying ? "⏸ Pause" : "▶ Play";
  });

  modalDirBtn.addEventListener("click", () => {
    simDirection *= -1;
    modalDirBtn.textContent = simDirection === 1 ? "⇄ Forward" : "⇄ Reverse";
  });

  modalResetBtn.addEventListener("click", () => {
    simElapsedYears = 0;
    modalTimeSlider.value = "0";
    modalManualPan = { x: 0, y: 0 };
    lastSimTick = performance.now();
  });

  modalFollowBtn.addEventListener("click", () => {
    modalFollowDwarf = !modalFollowDwarf;
    if (modalFollowDwarf) {
      modalManualPan = { x: 0, y: 0 };
    }
    syncModalHudAndControls();
  });

  modalRecenterBtn.addEventListener("click", () => {
    modalFollowDwarf = true;
    modalManualPan = { x: 0, y: 0 };
    syncModalHudAndControls();
  });

  speedPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      setSimSpeed(Number.parseFloat(pill.dataset.speed) || 1.0);
    });
  });

  modalSpeedSlider.addEventListener("input", (e) => {
    setSimSpeed(Number.parseFloat(e.target.value) || 1.0);
  });

  zoomPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      modalZoom = Number.parseFloat(pill.dataset.zoom) || 1.0;
      syncModalHudAndControls();
    });
  });

  modalZoomSlider.addEventListener("input", (e) => {
    modalZoom = Number.parseFloat(e.target.value) || 1.0;
    syncModalHudAndControls();
  });

  view3dPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      view3dPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      const mode = pill.dataset.view;
      if (mode === "top") modalPitch = 0.04;
      else if (mode === "side") modalPitch = 1.5;
      else modalPitch = 1.02;
    });
  });

  modalTimeSlider.addEventListener("input", (e) => {
    simElapsedYears = Number.parseFloat(e.target.value) || 0;
  });

  modalSimCanvas.addEventListener("mousedown", (e) => {
    isModalDragging = true;
    modalDragMode = e.shiftKey || e.button === 2 ? "pan" : "rotate";
    lastModalMouse = { x: e.clientX, y: e.clientY };
  });

  modalSimCanvas.addEventListener("contextmenu", (e) => e.preventDefault());

  window.addEventListener("mousemove", (e) => {
    if (!isModalDragging || !isModalOpen) return;
    const dx = e.clientX - lastModalMouse.x;
    const dy = e.clientY - lastModalMouse.y;
    lastModalMouse = { x: e.clientX, y: e.clientY };

    if (modalDragMode === "pan") {
      modalManualPan.x += dx;
      modalManualPan.y += dy;
    } else {
      modalYaw += dx * 0.008;
      modalPitch = Math.min(1.54, Math.max(0.02, modalPitch + dy * 0.008));
    }
  });

  window.addEventListener("mouseup", () => {
    isModalDragging = false;
  });

  modalSimCanvas.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.15 : 0.87;
      modalZoom = Math.min(8.0, Math.max(0.6, modalZoom * factor));
      syncModalHudAndControls();
    },
    { passive: false }
  );

  function projectModal3D(x, y, z, w, h) {
    const dx = x - modalCamFocus.x;
    const dy = y - modalCamFocus.y;
    const dz = z - modalCamFocus.z;

    const cosY = Math.cos(modalYaw);
    const sinY = Math.sin(modalYaw);
    const rx = dx * cosY - dy * sinY;
    const ry = dx * sinY + dy * cosY;
    const rz = dz;

    const cosP = Math.cos(modalPitch);
    const sinP = Math.sin(modalPitch);
    const camY = ry * cosP - rz * sinP;
    const camDepth = ry * sinP + rz * cosP;

    const fovDist = 900;
    const persp = fovDist / Math.max(180, fovDist + camDepth);
    const scale = modalZoom * persp;

    return {
      x: w * 0.5 + modalManualPan.x + rx * scale,
      y: h * 0.52 + modalManualPan.y + camY * scale,
      scale,
      depth: camDepth,
    };
  }

  function computeDwarfSimPos3D(target, yr) {
    const v = target.velVec3D || { x: 0.72, y: -0.5, z: 0.48 };
    const vLen = Math.hypot(v.x, v.y, v.z) || 1;
    const ux = v.x / vLen;
    const uy = v.y / vLen;
    const uz = v.z / vLen;

    const span = 420;
    const tNorm = yr / 15 - 0.5;
    let x = ux * span * tNorm;
    let y = uy * span * tNorm;
    let z = uz * span * tNorm;

    if (chkSimParallax.checked) {
      const wobbleAmp = target.simMode === "tno-arc" ? 15 : 9;
      const px = -uy;
      const py = ux;
      x += Math.cos(yr * Math.PI * 2) * wobbleAmp * px;
      y += Math.cos(yr * Math.PI * 2) * wobbleAmp * py;
      z += Math.sin(yr * Math.PI * 2) * (wobbleAmp * 0.65);
    }

    return { x, y, z, ux, uy, uz, span };
  }

  function renderModalSimulation(now) {
    if (!selectedTarget) return;
    const dt = lastSimTick ? Math.min((now - lastSimTick) / 1000, 0.05) : 0;
    lastSimTick = now;

    if (simPlaying && !prefersReducedMotion) {
      simElapsedYears += dt * 0.85 * simSpeed * simDirection;
      if (simElapsedYears > 15) simElapsedYears = 0;
      if (simElapsedYears < 0) simElapsedYears = 15;
      modalTimeSlider.value = simElapsedYears.toFixed(2);
    }

    const currentYear = 2020 + simElapsedYears;
    const annualB = selectedTarget.trajPerYearBillions || 0;
    const totalTraveledB = simElapsedYears * annualB;

    hudSimYear.textContent = currentYear.toFixed(2);
    modalYearReadout.textContent = currentYear.toFixed(1);
    hudSimKm.textContent = annualB ? `${totalTraveledB.toFixed(2)} × 10⁹ km` : "Unknown";

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = modalSimCanvas.width / dpr;
    const h = modalSimCanvas.height / dpr;
    const ctx = modalSimCtx;
    const enc = getEncodingForTarget(selectedTarget);

    const curState = computeDwarfSimPos3D(selectedTarget, simElapsedYears);

    // AUTO-FOLLOW FIX: Smoothly lock 3D camera focus onto the moving dwarf
    if (modalFollowDwarf) {
      modalCamFocus.x += (curState.x - modalCamFocus.x) * 0.25;
      modalCamFocus.y += (curState.y - modalCamFocus.y) * 0.25;
      modalCamFocus.z += (curState.z - modalCamFocus.z) * 0.25;
    }

    ctx.fillStyle = "#000001";
    ctx.fillRect(0, 0, w, h);

    if (chkSimGrid.checked) {
      ctx.strokeStyle = "rgba(237, 240, 247, 0.08)";
      ctx.lineWidth = 1;
      const gridExtent = 320;
      const gridStep = 40;
      for (let g = -gridExtent; g <= gridExtent; g += gridStep) {
        const a1 = projectModal3D(g, -gridExtent, 0, w, h);
        const a2 = projectModal3D(g, gridExtent, 0, w, h);
        ctx.beginPath();
        ctx.moveTo(a1.x, a1.y);
        ctx.lineTo(a2.x, a2.y);
        ctx.stroke();

        const b1 = projectModal3D(-gridExtent, g, 0, w, h);
        const b2 = projectModal3D(gridExtent, g, 0, w, h);
        ctx.beginPath();
        ctx.moveTo(b1.x, b1.y);
        ctx.lineTo(b2.x, b2.y);
        ctx.stroke();
      }
    }

    for (let i = 0; i < 85; i++) {
      const sx = (seededRand(i + 500) - 0.5) * 760;
      const sy = (seededRand(i + 600) - 0.5) * 760;
      const sz = (seededRand(i + 700) - 0.5) * 420;
      const sp = projectModal3D(sx, sy, sz, w, h);
      if (sp.x < -10 || sp.x > w + 10 || sp.y < -10 || sp.y > h + 10) continue;

      ctx.fillStyle = "rgba(237, 240, 247, 0.42)";
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, 0.7 + seededRand(i + 750) * 1.1, 0, Math.PI * 2);
      ctx.fill();
    }

    if (chkSimTrail.checked) {
      const pStart = projectModal3D(
        -curState.ux * curState.span * 0.5,
        -curState.uy * curState.span * 0.5,
        -curState.uz * curState.span * 0.5,
        w,
        h
      );
      const pEnd = projectModal3D(
        curState.ux * curState.span * 0.5,
        curState.uy * curState.span * 0.5,
        curState.uz * curState.span * 0.5,
        w,
        h
      );

      ctx.strokeStyle = `rgba(${enc.rgb}, 0.25)`;
      ctx.lineWidth = 1.3;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(pStart.x, pStart.y);
      ctx.lineTo(pEnd.x, pEnd.y);
      ctx.stroke();
      ctx.setLineDash([]);

      const pStartGround = projectModal3D(
        -curState.ux * curState.span * 0.5,
        -curState.uy * curState.span * 0.5,
        0,
        w,
        h
      );
      const pEndGround = projectModal3D(
        curState.ux * curState.span * 0.5,
        curState.uy * curState.span * 0.5,
        0,
        w,
        h
      );
      ctx.strokeStyle = "rgba(139, 147, 167, 0.16)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pStartGround.x, pStartGround.y);
      ctx.lineTo(pEndGround.x, pEndGround.y);
      ctx.stroke();

      ctx.strokeStyle = enc.hex;
      ctx.lineWidth = 2.4;
      ctx.beginPath();
      const steps = Math.max(2, Math.round(simElapsedYears * 16));
      for (let s = 0; s <= steps; s++) {
        const yr = (s / steps) * simElapsedYears;
        const pos = computeDwarfSimPos3D(selectedTarget, yr);
        const pp = projectModal3D(pos.x, pos.y, pos.z, w, h);
        if (s === 0) ctx.moveTo(pp.x, pp.y);
        else ctx.lineTo(pp.x, pp.y);
      }
      ctx.stroke();

      [0, 3, 6, 9, 12, 15].forEach((yrMark) => {
        const tMark = yrMark / 15 - 0.5;
        const mp = projectModal3D(
          curState.ux * curState.span * tMark,
          curState.uy * curState.span * tMark,
          curState.uz * curState.span * tMark,
          w,
          h
        );
        ctx.fillStyle = yrMark <= simElapsedYears ? enc.hex : "rgba(139, 147, 167, 0.55)";
        ctx.beginPath();
        ctx.arc(mp.x, mp.y, 3.2, 0, Math.PI * 2);
        ctx.fill();

        ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, monospace";
        ctx.textAlign = "center";
        ctx.fillText(String(2020 + yrMark), mp.x, mp.y + 15);
      });
    }

    const pDwarf = projectModal3D(curState.x, curState.y, curState.z, w, h);
    const pGround = projectModal3D(curState.x, curState.y, 0, w, h);

    ctx.strokeStyle = `rgba(${enc.rgb}, 0.42)`;
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 2]);
    ctx.beginPath();
    ctx.moveTo(pGround.x, pGround.y);
    ctx.lineTo(pDwarf.x, pDwarf.y);
    ctx.stroke();
    ctx.setLineDash([]);

    if (chkSimVector.checked) {
      const vecLen3D = 48 * simDirection;
      const pTip = projectModal3D(
        curState.x + curState.ux * vecLen3D,
        curState.y + curState.uy * vecLen3D,
        curState.z + curState.uz * vecLen3D,
        w,
        h
      );

      ctx.strokeStyle = "#edf0f7";
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.moveTo(pDwarf.x, pDwarf.y);
      ctx.lineTo(pTip.x, pTip.y);
      ctx.stroke();

      const ang2D = Math.atan2(pTip.y - pDwarf.y, pTip.x - pDwarf.x);
      ctx.fillStyle = "#edf0f7";
      ctx.beginPath();
      ctx.moveTo(pTip.x, pTip.y);
      ctx.lineTo(pTip.x - 8 * Math.cos(ang2D - 0.4), pTip.y - 8 * Math.sin(ang2D - 0.4));
      ctx.lineTo(pTip.x - 8 * Math.cos(ang2D + 0.4), pTip.y - 8 * Math.sin(ang2D + 0.4));
      ctx.closePath();
      ctx.fill();

      ctx.font = "10.5px ui-monospace, SFMono-Regular, Menlo, monospace";
      ctx.textAlign = "left";
      ctx.fillText(`v₃D = ${selectedTarget.velocityKms}`, pTip.x + 8, pTip.y + 3);
    }

    const visualScale = Math.min(2.2, Math.max(0.85, Math.sqrt(modalZoom)));

    if (selectedTarget.simMode === "binary-orbit") {
      const orbitAngle = simElapsedYears * 2.5;
      const sep = 15;
      const b1 = projectModal3D(
        curState.x + Math.cos(orbitAngle) * sep,
        curState.y + Math.sin(orbitAngle) * sep,
        curState.z + Math.sin(orbitAngle) * 5,
        w,
        h
      );
      const b2 = projectModal3D(
        curState.x - Math.cos(orbitAngle) * sep,
        curState.y - Math.sin(orbitAngle) * sep,
        curState.z - Math.sin(orbitAngle) * 5,
        w,
        h
      );

      ctx.strokeStyle = `rgba(${enc.rgb}, 0.35)`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(b1.x, b1.y);
      ctx.lineTo(b2.x, b2.y);
      ctx.stroke();

      ctx.fillStyle = "#edf0f7";
      ctx.beginPath();
      ctx.arc(b1.x, b1.y, 5.2 * visualScale, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = enc.hex;
      ctx.beginPath();
      ctx.arc(b2.x, b2.y, 4.0 * visualScale, 0, Math.PI * 2);
      ctx.fill();
    } else if (selectedTarget.simMode === "dust-pulsation") {
      const pulsePhase = Math.sin(simElapsedYears * 5.2);
      const coronaR = (26 + pulsePhase * 8) * visualScale;
      const g = ctx.createRadialGradient(pDwarf.x, pDwarf.y, 2, pDwarf.x, pDwarf.y, coronaR);
      g.addColorStop(0, `rgba(${enc.rgb}, 0.92)`);
      g.addColorStop(0.55, `rgba(${enc.rgb}, 0.28)`);
      g.addColorStop(1, `rgba(${enc.rgb}, 0)`);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(pDwarf.x, pDwarf.y, coronaR, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#edf0f7";
      ctx.beginPath();
      ctx.arc(pDwarf.x, pDwarf.y, (5.5 + pulsePhase * 1.4) * visualScale, 0, Math.PI * 2);
      ctx.fill();
    } else {
      const glowR = 25 * visualScale;
      const g = ctx.createRadialGradient(pDwarf.x, pDwarf.y, 2, pDwarf.x, pDwarf.y, glowR);
      g.addColorStop(0, `rgba(${enc.rgb}, 0.95)`);
      g.addColorStop(0.45, `rgba(${enc.rgb}, 0.3)`);
      g.addColorStop(1, `rgba(${enc.rgb}, 0)`);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(pDwarf.x, pDwarf.y, glowR, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#edf0f7";
      ctx.beginPath();
      ctx.arc(pDwarf.x, pDwarf.y, 4.8 * visualScale, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = enc.hex;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.arc(pDwarf.x, pDwarf.y, 9.5 * visualScale, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  // =========================================================
  // 13. Pop-up 2 (F2): Two-Date Side-by-Side Comparison Modal
  // =========================================================
  function openCompareModal() {
    const target = selectedTarget || DWARF_TARGETS[0];
    if (!frames.length) {
      selectAndZoomToTarget(target).then(() => {
        populateCompareModal(target);
      });
      return;
    }
    populateCompareModal(target);
  }

  function populateCompareModal(target) {
    compareModalTitle.textContent = `${target.shortName || target.name} — Before / After Epoch Comparison`;
    compareSelectA.innerHTML = "";
    compareSelectB.innerHTML = "";

    frames.forEach((f, idx) => {
      const optA = document.createElement("option");
      optA.value = String(idx);
      optA.textContent = `Epoch ${idx + 1}: ${f.date}`;
      compareSelectA.appendChild(optA);

      const optB = document.createElement("option");
      optB.value = String(idx);
      optB.textContent = `Epoch ${idx + 1}: ${f.date}`;
      compareSelectB.appendChild(optB);
    });

    compareSelectA.value = "0";
    compareSelectB.value = String(currentIndex > 0 ? currentIndex : Math.min(1, frames.length - 1));
    renderCompareFrames();
    compareModalBackdrop.classList.remove("is-closed");
  }

  function renderCompareFrames() {
    if (!frames.length) return;
    const fA = frames[Number(compareSelectA.value) || 0] || frames[0];
    const fB = frames[Number(compareSelectB.value) || 0] || frames[frames.length - 1];

    if (fA.imageUrl) compareImgA.src = fA.imageUrl;
    if (fB.imageUrl) compareImgB.src = fB.imageUrl;

    compareMetaDateA.textContent = `Date: ${fA.date}`;
    compareMetaBandA.textContent = fA.band;
    compareMetaFovA.textContent = `FOV: ${fA.fov || `${fovSelect.value} arcmin`}`;

    compareMetaDateB.textContent = `Date: ${fB.date}`;
    compareMetaBandB.textContent = fB.band;
    compareMetaFovB.textContent = `FOV: ${fB.fov || `${fovSelect.value} arcmin`}`;
    requestAnimationFrame(drawCompareMarkers);
  }

  // --- Repère de la cible dans « Compare 2 Dates » : les images fixes sont exactement les
  // images de la vidéo, donc les positions (pixels vidéo) s'y appliquent directement.
  const compareMarkerA = document.getElementById("compare-marker-a");
  const compareMarkerB = document.getElementById("compare-marker-b");
  const compareMarkerToggle = document.getElementById("compare-marker-toggle");

  function drawTargetRing(ctx, p, r, measured, solid) {
    ctx.save();
    ctx.lineWidth = solid ? 2 : 1.4;
    ctx.strokeStyle = solid ? (measured ? "#00e5ff" : "rgba(220,220,220,0.95)") : "rgba(255,255,255,0.7)";
    if (!solid || !measured) ctx.setLineDash([4, 3]);
    ctx.shadowColor = "rgba(0,0,0,0.9)";
    ctx.shadowBlur = 4;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.stroke();
    if (solid) {
      ctx.setLineDash([]);
      ctx.beginPath();
      [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
        ctx.moveTo(p.x + dx * (r + 4), p.y + dy * (r + 4));
        ctx.lineTo(p.x + dx * (r + 12), p.y + dy * (r + 12));
      });
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawArrow(ctx, a, b) {
    const dx = b.x - a.x, dy = b.y - a.y, L = Math.hypot(dx, dy);
    if (L < 6) return;                          // pas de déplacement visible
    const ux = dx / L, uy = dy / L, h = Math.min(10, L * 0.4);
    ctx.save();
    ctx.strokeStyle = "#ffb547";
    ctx.fillStyle = "#ffb547";
    ctx.lineWidth = 2;
    ctx.shadowColor = "rgba(0,0,0,0.9)";
    ctx.shadowBlur = 4;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x - ux * h, b.y - uy * h);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(b.x, b.y);
    ctx.lineTo(b.x - ux * h - uy * h * 0.55, b.y - uy * h + ux * h * 0.55);
    ctx.lineTo(b.x - ux * h + uy * h * 0.55, b.y - uy * h - ux * h * 0.55);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawCompareMarkers() {
    const fA = frames[Number(compareSelectA?.value) || 0];
    const fB = frames[Number(compareSelectB?.value) || 0];
    [[compareMarkerA, compareImgA, fA, fB, false], [compareMarkerB, compareImgB, fB, fA, true]]
      .forEach(([cv, img, f, other, isB]) => {
        if (!cv || !img) return;
        const box = cv.parentElement;
        const W = box.clientWidth, H = box.clientHeight;
        const dpr = window.devicePixelRatio || 1;
        cv.width = Math.round(W * dpr);
        cv.height = Math.round(H * dpr);
        const ctx = cv.getContext("2d");
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, W, H);
        if (compareMarkerToggle && !compareMarkerToggle.checked) return;
        const nw = img.naturalWidth, nh = img.naturalHeight;
        if (!f || !nw || !nh || !img.complete) return;
        const k = Math.min(W / nw, H / nh);             // object-fit: contain
        const ox = (W - nw * k) / 2, oy = (H - nh * k) / 2;
        const P = (q) => ({ x: ox + q.x * k, y: oy + q.y * k });
        const r = Math.min(34, Math.max(10, 2.5 * (videoInfo?.pxScale || 6) * k));
        const here = f.markerMeasured || f.markerPredicted;
        const there = other && other !== f ? other.markerMeasured || other.markerPredicted : null;
        if (there) drawTargetRing(ctx, P(there), r, true, false);
        if (here && there) {
          // la flèche va toujours de la date A vers la date B
          isB ? drawArrow(ctx, P(there), P(here)) : drawArrow(ctx, P(here), P(there));
        }
        if (here) drawTargetRing(ctx, P(here), r, !!f.markerMeasured, true);
      });
  }

  compareImgA?.addEventListener("load", drawCompareMarkers);
  compareImgB?.addEventListener("load", drawCompareMarkers);
  compareMarkerToggle?.addEventListener("change", drawCompareMarkers);
  window.addEventListener("resize", () => {
    if (!compareModalBackdrop?.classList.contains("is-closed")) drawCompareMarkers();
  });

  function closeCompareModal() {
    compareModalBackdrop.classList.add("is-closed");
  }

  openCompareModalBtn?.addEventListener("click", openCompareModal);
  inspectorCompareTrigger?.addEventListener("click", openCompareModal);
  closeCompareModalBtn?.addEventListener("click", closeCompareModal);
  compareModalBackdrop?.addEventListener("click", (e) => {
    if (e.target === compareModalBackdrop) closeCompareModal();
  });
  compareSelectA?.addEventListener("change", renderCompareFrames);
  compareSelectB?.addEventListener("change", renderCompareFrames);

  // « Full » : ouvre la grande fenêtre vidéo SPHEREx (la même qu'au clic sur l'objet)
  cutoutFullscreenBtn?.addEventListener("click", () => {
    openVideoModal(selectedTarget);
  });

  // =========================================================
  // 14. Synthetic WCS Cutout & 102-Channel Spectrum Renderers
  // =========================================================
  const REF_STARS = [
    { x: 34, y: 28, r: 1.5, a: 0.78 },
    { x: 86, y: 112, r: 1.8, a: 0.85 },
    { x: 118, y: 36, r: 1.2, a: 0.6 },
    { x: 215, y: 30, r: 1.9, a: 0.88 },
    { x: 248, y: 118, r: 1.4, a: 0.72 },
    { x: 56, y: 82, r: 1.1, a: 0.52 },
    { x: 194, y: 96, r: 1.6, a: 0.8 },
    { x: 264, y: 64, r: 1.2, a: 0.64 },
    { x: 148, y: 128, r: 1.3, a: 0.62 },
  ];

  function renderCutout(target, epochIdx, totalEpochs) {
    const w = cutoutCanvas.width;
    const h = cutoutCanvas.height;
    const cx = w / 2;
    const cy = h / 2;

    cutoutCtx.clearRect(0, 0, w, h);

    if (!diffSubtractionMode) {
      cutoutCtx.strokeStyle = "rgba(56, 178, 172, 0.14)";
      cutoutCtx.lineWidth = 1;
      for (let gx = 29; gx < w; gx += 58) {
        cutoutCtx.beginPath();
        cutoutCtx.moveTo(gx, 0);
        cutoutCtx.lineTo(gx, h);
        cutoutCtx.stroke();
      }
      for (let gy = 25; gy < h; gy += 50) {
        cutoutCtx.beginPath();
        cutoutCtx.moveTo(0, gy);
        cutoutCtx.lineTo(w, gy);
        cutoutCtx.stroke();
      }

      REF_STARS.forEach((s) => {
        cutoutCtx.fillStyle = `rgba(237, 240, 247, ${s.a})`;
        cutoutCtx.beginPath();
        cutoutCtx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        cutoutCtx.fill();
      });
    } else {
      cutoutCtx.fillStyle = "rgba(139, 147, 167, 0.8)";
      cutoutCtx.font = "9px ui-monospace, SFMono-Regular, Menlo, monospace";
      cutoutCtx.textAlign = "left";
      cutoutCtx.fillText("DIFF: EPOCH(t) − EPOCH(1)", 8, 13);
    }

    const m = target.motionPerEpoch || { dx: 10, dy: -8, pulse: 0 };
    const tOffset = epochIdx - (totalEpochs - 1) / 2;
    const e1Offset = 0 - (totalEpochs - 1) / 2;

    const tx = cx + tOffset * m.dx;
    const ty = cy + tOffset * m.dy;
    const e1x = cx + e1Offset * m.dx;
    const e1y = cy + e1Offset * m.dy;

    const enc = getEncodingForTarget(target);
    const pulseFactor = m.pulse ? 1 + Math.sin(epochIdx * 1.6) * m.pulse : 1;
    const psfRadius = 7.5 * pulseFactor;

    if (diffSubtractionMode && epochIdx > 0) {
      cutoutCtx.strokeStyle = "rgba(56, 178, 172, 0.9)";
      cutoutCtx.lineWidth = 1.5;
      cutoutCtx.setLineDash([2, 2]);
      cutoutCtx.beginPath();
      cutoutCtx.arc(e1x, e1y, 8, 0, Math.PI * 2);
      cutoutCtx.stroke();
      cutoutCtx.setLineDash([]);
    }

    const grad = cutoutCtx.createRadialGradient(tx, ty, 1, tx, ty, psfRadius * 2.5);
    grad.addColorStop(0, "rgba(237, 240, 247, 0.95)");
    grad.addColorStop(0.4, `rgba(${enc.rgb}, 0.65)`);
    grad.addColorStop(1, `rgba(${enc.rgb}, 0)`);
    cutoutCtx.fillStyle = grad;
    cutoutCtx.beginPath();
    cutoutCtx.arc(tx, ty, psfRadius * 2.5, 0, Math.PI * 2);
    cutoutCtx.fill();

    cutoutCtx.strokeStyle = enc.hex;
    cutoutCtx.lineWidth = 1.2;
    cutoutCtx.strokeRect(tx - 13, ty - 13, 26, 26);

    cutoutEpochLabel.textContent = `Epoch ${epochIdx + 1} / ${totalEpochs}`;
  }

  function renderSpectrumPlot(target) {
    const w = spectrumCanvas.width;
    const h = spectrumCanvas.height;
    const profile = target.spectrumProfile || [0.5, 0.6, 0.7, 0.8, 0.7, 0.6, 0.5, 0.6, 0.7, 0.8, 0.7, 0.6];
    const enc = getEncodingForTarget(target);

    spectrumCtx.fillStyle = "#000001";
    spectrumCtx.fillRect(0, 0, w, h);

    spectrumCtx.strokeStyle = "rgba(139, 147, 167, 0.14)";
    spectrumCtx.lineWidth = 1;
    [18, 36, 54].forEach((y) => {
      spectrumCtx.beginPath();
      spectrumCtx.moveTo(8, y);
      spectrumCtx.lineTo(w - 8, y);
      spectrumCtx.stroke();
    });

    const padX = 14;
    const plotW = w - padX * 2;
    const stepX = plotW / (profile.length - 1);

    spectrumCtx.beginPath();
    profile.forEach((val, idx) => {
      const px = padX + idx * stepX;
      const py = h - 12 - val * (h - 24);
      if (idx === 0) spectrumCtx.moveTo(px, py);
      else spectrumCtx.lineTo(px, py);
    });
    spectrumCtx.strokeStyle = enc.hex;
    spectrumCtx.lineWidth = 1.8;
    spectrumCtx.stroke();

    profile.forEach((val, idx) => {
      const px = padX + idx * stepX;
      const py = h - 12 - val * (h - 24);
      spectrumCtx.fillStyle = "#edf0f7";
      spectrumCtx.beginPath();
      spectrumCtx.arc(px, py, 2.1, 0, Math.PI * 2);
      spectrumCtx.fill();
    });
  }

  // bouton « Diff » retiré de l'interface
  diffModeBtn?.addEventListener("click", () => {
    diffSubtractionMode = !diffSubtractionMode;
    diffModeBtn.textContent = diffSubtractionMode ? "Diff: ON" : "Diff: OFF";
    diffModeBtn.classList.toggle("active", diffSubtractionMode);
    if (selectedTarget && frames.length) {
      renderCutout(selectedTarget, currentIndex, frames.length);
    }
  });

  // =========================================================
  // 15. F1 Coordinate Form Validation (RA 0..360, Dec -90..+90)
  // =========================================================
  function clearInputErrors() {
    raInput.closest(".field-group").classList.remove("input-error");
    decInput.closest(".field-group").classList.remove("input-error");
    fovSelect.closest(".field-group")?.classList.remove("input-error");
    formError.textContent = "";
    formError.classList.remove("visible");
  }

  function showInputError(inputEl, message) {
    inputEl.closest(".field-group").classList.add("input-error");
    formError.textContent = message;
    formError.classList.add("visible");
    inputEl.focus();
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    clearInputErrors();

    const rawRa = raInput.value.trim().replace(/,/g, ".");
    const rawDec = decInput.value.trim().replace(/,/g, ".").replace("−", "-");
    const raNum = Number(rawRa);
    const decNum = Number(rawDec);

    if (!rawRa || !Number.isFinite(raNum) || raNum < 0 || raNum > 360) {
      showInputError(raInput, "Right Ascension (RA) must be between 0° and 360°.");
      return;
    }
    if (!rawDec || !Number.isFinite(decNum) || decNum < -90 || decNum > 90) {
      showInputError(decInput, "Declination (Dec) must be between −90° and +90°.");
      return;
    }
    // FOV libre : toute valeur entre 1' et 12' (limite du serveur : au-delà, les images
    // à télécharger deviennent trop lourdes)
    const fovNum = Number(fovSelect.value.trim().replace(/,/g, "."));
    if (!Number.isFinite(fovNum) || fovNum < 1 || fovNum > 12) {
      showInputError(fovSelect, "Le champ de vue (FOV) doit être entre 1 et 12 minutes d'arc.");
      return;
    }
    fovSelect.value = String(fovNum);

    const matched = getAllTargets().find(
      (t) =>
        Math.abs(Number.parseFloat(t.ra) - raNum) < 0.05 &&
        Math.abs(Number.parseFloat(t.dec) - decNum) < 0.05
    );

    if (matched) {
      selectAndZoomToTarget(matched);
      return;
    }

    const targetGalId = activeGalaxyId === "all" ? "milky-way" : activeGalaxyId;
    const rad = (raNum * Math.PI) / 180;
    const r = 32 + ((Math.abs(decNum) / 90) * 85);

    customTrackedTarget = {
      id: "custom-field",
      galaxyId: targetGalId,
      name: `ICRS J${raNum.toFixed(2)}${decNum >= 0 ? "+" : ""}${decNum.toFixed(2)}`,
      shortName: `Custom (${raNum.toFixed(1)}°, ${decNum.toFixed(1)}°)`,
      type: "Custom ICRS Sky Field",
      spectral: "IR Source",
      temp: "N/A",
      distanceLy: "Field Cutout",
      distanceKm: "N/A",
      velocityKms: "48.0 km/s",
      velocityNum: 48.0,
      velocityKmh: "172,800 km/h",
      velComponents: "Custom Field Vector",
      properMotion: "320 mas/yr",
      properMotionNum: 320,
      trajPerYearKm: "1.51 × 10⁹ km/yr",
      trajPerYearBillions: 1.51,
      trajPerEpochKm: "+755M km / 6-mo",
      mass: "N/A",
      radiusKm: "N/A",
      constellation: "ICRS SKY",
      discovery: "User Query",
      age: "N/A",
      flag: "FLAGS: 0x00 NOMINAL",
      ra: raNum.toFixed(4),
      dec: decNum.toFixed(4),
      local3D: {
        x: Math.round(Math.cos(rad) * r),
        y: Math.round(Math.sin(rad) * r),
        z: Math.round((decNum / 90) * 45),
      },
      velVec3D: { x: 0.65, y: 0.55, z: 0.52 },
      trajSpan3D: 42,
      simMode: "parallax-drift",
      summary: `Custom SPHEREx sky pointing centered at RA ${raNum.toFixed(4)}°, Dec ${decNum.toFixed(4)}° across a ${fovSelect.value}-arcminute field of view.`,
      desc: `Custom SPHEREx sky pointing centered at RA ${raNum.toFixed(4)}°, Dec ${decNum.toFixed(4)}°.`,
      motionPerEpoch: { dx: 6, dy: -4, pulse: 0 },
      spectrumProfile: [0.4, 0.48, 0.55, 0.62, 0.58, 0.66, 0.71, 0.68, 0.74, 0.79, 0.72, 0.65],
    };

    selectAndZoomToTarget(customTrackedTarget);
  });

  // =========================================================
  // 16. F3 Epoch Timeline & Blink Comparator Controls
  // =========================================================
  let frames = [];
  let currentIndex = 0;
  let timerId = null;

  // --- Mode vidéo : le backend renvoie UNE vidéo MP4 + la frise (une entrée par image).
  // La vidéo est la source de vérité : la case de détails suit la vidéo, et changer
  // la date (points, curseur, Prev/Next) déplace la vidéo à cette date.
  let videoMode = false;
  let syncingFromVideo = false;

  function setPlayButtons(playing) {
    playBtn.classList.toggle("primary", playing);
    pauseBtn.classList.toggle("primary", !playing);
  }

  function syncFromVideo() {
    if (!videoMode || !frames.length || !cutoutVideo) return;
    const idx = window.ObservationsApi?.indexAtTime
      ? window.ObservationsApi.indexAtTime(frames, cutoutVideo.currentTime)
      : currentIndex;
    if (idx !== currentIndex) {
      syncingFromVideo = true;
      try {
        goToEpoch(idx);
      } finally {
        syncingFromVideo = false;
      }
    }
  }

  function videoRafLoop() {
    syncFromVideo();
    if (videoMode && cutoutVideo && !cutoutVideo.paused && !cutoutVideo.ended) {
      requestAnimationFrame(videoRafLoop);
    }
  }

  // --- Repère de la cible : dessiné par le front par-dessus la vidéo propre
  // (la vidéo reste l'image brute du ciel ; positions fournies par le backend).
  let showMarkers = true;
  let videoInfo = null;

  function drawMarkers() {
    if (!markerCanvas) return;
    const stage = markerCanvas.parentElement;
    const W = stage.clientWidth, H = stage.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    if (markerCanvas.width !== Math.round(W * dpr) || markerCanvas.height !== Math.round(H * dpr)) {
      markerCanvas.width = Math.round(W * dpr);
      markerCanvas.height = Math.round(H * dpr);
    }
    const ctx = markerCanvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    if (!showMarkers || !videoMode || !frames.length) return;
    const vw = cutoutVideo.videoWidth || videoInfo?.width;
    const vh = cutoutVideo.videoHeight || videoInfo?.height;
    if (!vw || !vh) return;
    // object-fit: contain -> échelle et décalage de l'image dans le panneau
    const k = Math.min(W / vw, H / vh);
    const ox = (W - vw * k) / 2, oy = (H - vh * k) / 2;
    const P = (p) => ({ x: ox + p.x * k, y: oy + p.y * k });

    // trajectoire ajustée (positions prédites), discrète
    const pred = frames.map((f) => f.markerPredicted).filter(Boolean).map(P);
    if (pred.length > 1) {
      ctx.strokeStyle = "rgba(255,255,255,0.45)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      pred.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
      ctx.stroke();
      ctx.setLineDash([]);
    }
    // positions mesurées jusqu'à l'image courante
    frames.slice(0, currentIndex).forEach((f) => {
      if (!f.markerMeasured) return;
      const p = P(f.markerMeasured);
      ctx.fillStyle = "rgba(0,229,255,0.55)";
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
    // cible dans l'image courante : cercle plein = mesurée, pointillé = seulement prédite
    const f = frames[currentIndex];
    const pos = f?.markerMeasured || f?.markerPredicted;
    if (!pos) return;
    const p = P(pos);
    const r = Math.min(30, Math.max(8, 2.5 * (videoInfo?.pxScale || 6) * k)); // ≈ 2,5 px SPHEREx
    ctx.strokeStyle = f.markerMeasured && f.usedInFit ? "#00e5ff" : "rgba(200,200,200,0.9)";
    ctx.lineWidth = 1.6;
    if (!f.markerMeasured) ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    // petites graduations pour bien voir la cible
    ctx.beginPath();
    [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
      ctx.moveTo(p.x + dx * (r + 3), p.y + dy * (r + 3));
      ctx.lineTo(p.x + dx * (r + 9), p.y + dy * (r + 9));
    });
    ctx.stroke();
  }

  if (markerToggleBtn) {
    markerToggleBtn.addEventListener("click", () => {
      showMarkers = !showMarkers;
      markerToggleBtn.textContent = showMarkers ? "◎ Cible: ON" : "◎ Cible: OFF";
      markerToggleBtn.classList.toggle("active", showMarkers);
      drawMarkers();
    });
  }
  window.addEventListener("resize", drawMarkers);
  document.addEventListener("fullscreenchange", () => setTimeout(drawMarkers, 50));
  if (cutoutVideo) cutoutVideo.addEventListener("loadedmetadata", drawMarkers);

  function clearVideo() {
    videoMode = false;
    videoInfo = null;
    drawMarkers();
    if (!cutoutVideo) return;
    cutoutVideo.pause();
    cutoutVideo.removeAttribute("src");
    cutoutVideo.load();
  }

  if (cutoutVideo) {
    cutoutVideo.addEventListener("play", () => {
      setPlayButtons(true);
      requestAnimationFrame(videoRafLoop);
    });
    cutoutVideo.addEventListener("pause", () => setPlayButtons(false));
    cutoutVideo.addEventListener("ended", () => setPlayButtons(false));
    cutoutVideo.addEventListener("timeupdate", syncFromVideo);
    cutoutVideo.addEventListener("seeked", syncFromVideo);
  }

  function renderDots() {
    ticksEl.innerHTML = "";
    frames.forEach((f, idx) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "tl-dot" + (idx === currentIndex ? " active" : "");
      dot.title = f.date;
      dot.setAttribute("aria-label", `Epoch ${idx + 1}: ${f.date}`);
      dot.addEventListener("click", () => {
        stopPlayback();
        goToEpoch(idx);
      });
      ticksEl.appendChild(dot);
    });
  }

  function goToEpoch(idx) {
    if (!frames.length) return;
    currentIndex = ((idx % frames.length) + frames.length) % frames.length;
    const frame = frames[currentIndex];

    badgeEl.textContent = `Epoch ${currentIndex + 1} / ${frames.length}`;
    dateEl.textContent = frame.date;
    bandEl.textContent = frame.band ? `• ${frame.band}` : "";
    slider.value = String(currentIndex);

    Array.from(ticksEl.children).forEach((dot, i) => {
      dot.classList.toggle("active", i === currentIndex);
    });

    if (videoMode) {
      // la date a été changée par l'utilisateur -> la vidéo va à cette date
      if (!syncingFromVideo && typeof frame.videoTime === "number" &&
          Math.abs(cutoutVideo.currentTime - frame.videoTime) > 0.05) {
        cutoutVideo.currentTime = frame.videoTime;
      }
    } else if (frame.imageUrl && cutoutImg) {
      cutoutImg.src = frame.imageUrl;
    }
    bandEl.title = frame.note || "";
    setReadout(roDateEl, frame.dateUtc ? frame.dateUtc.replace("T", "  ").slice(0, 17) : frame.date);
    setReadout(roDetEl, frame.detector || "");
    setReadout(roWlEl, typeof frame.wavelengthUm === "number" ? `${frame.wavelengthUm.toFixed(3)} µm` : "");
    if (epochNoteEl) {
      // à droite : en grand pour un désaccord, discret pour les autres remarques
      const important = /^[⚠ℹ]/.test(frame.note || "");
      epochNoteEl.textContent = important ? frame.note : "";
      epochNoteEl.classList.toggle("warn", (frame.note || "").startsWith("⚠"));
      epochNoteEl.classList.toggle("info", (frame.note || "").startsWith("ℹ"));
    }
    drawMarkers();

    if (selectedTarget) {
      renderCutout(selectedTarget, currentIndex, frames.length);
    }

    window.dispatchEvent(
      new CustomEvent("spherex:epochChanged", {
        detail: { index: currentIndex, frame },
      })
    );
  }

  function startPlayback() {
    if (videoMode) {
      if (cutoutVideo.ended) cutoutVideo.currentTime = 0;
      cutoutVideo.play().catch(() => {});
      setPlayButtons(true);
      return;
    }
    if (timerId || frames.length <= 1) return;
    playBtn.classList.add("primary");
    pauseBtn.classList.remove("primary");
    timerId = window.setInterval(() => goToEpoch(currentIndex + 1), 1200 / (playRate || 1));
  }

  function stopPlayback() {
    if (videoMode && cutoutVideo && !cutoutVideo.paused) cutoutVideo.pause();
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
    playBtn.classList.remove("primary");
    pauseBtn.classList.add("primary");
  }

  function togglePlayback() {
    if (videoMode) {
      cutoutVideo.paused || cutoutVideo.ended ? startPlayback() : stopPlayback();
      return;
    }
    timerId ? stopPlayback() : startPlayback();
  }

  prevBtn.addEventListener("click", () => {
    stopPlayback();
    goToEpoch(currentIndex - 1);
  });

  nextBtn.addEventListener("click", () => {
    stopPlayback();
    goToEpoch(currentIndex + 1);
  });

  playBtn.addEventListener("click", startPlayback);
  pauseBtn.addEventListener("click", stopPlayback);

  // --- Vitesse de lecture : barre de boutons ×0.25 … ×4 (molette et touches - / + aussi)
  const speedControl = document.getElementById("speed-control");
  const speedBtns = Array.from(document.querySelectorAll("#speed-control .sc-btn"));
  const SPEED_RATES = speedBtns.map((b) => Number(b.dataset.rate));
  let playRate = 1;

  function setPlayRate(rate) {
    playRate = rate;
    if (cutoutVideo) {
      cutoutVideo.defaultPlaybackRate = rate;     // garde la vitesse quand la vidéo change
      cutoutVideo.playbackRate = rate;
    }
    speedBtns.forEach((b) => {
      const on = Number(b.dataset.rate) === rate;
      b.classList.toggle("active", on);
      b.setAttribute("aria-pressed", String(on));
    });
    speedControl?.classList.toggle("fast", rate > 1);
    speedControl?.classList.toggle("slow", rate < 1);
    // petit « flash » pour montrer que la vitesse a changé
    speedControl?.classList.remove("bump");
    void speedControl?.offsetWidth;
    speedControl?.classList.add("bump");
    if (!videoMode && timerId) {                  // ancien mode images : relance au bon rythme
      stopPlayback();
      startPlayback();
    }
  }

  function stepPlayRate(dir) {
    const i = SPEED_RATES.indexOf(playRate);
    const next = SPEED_RATES[Math.min(SPEED_RATES.length - 1, Math.max(0, i + dir))];
    if (next !== playRate) setPlayRate(next);
  }

  speedBtns.forEach((b) => b.addEventListener("click", () => setPlayRate(Number(b.dataset.rate))));
  speedControl?.addEventListener("wheel", (e) => {
    e.preventDefault();
    stepPlayRate(e.deltaY < 0 ? 1 : -1);
  }, { passive: false });
  document.addEventListener("keydown", (e) => {
    const tag = (e.target?.tagName || "").toLowerCase();
    if (tag === "input" || tag === "select" || tag === "textarea") return;
    if (!frames.length) return;
    if (e.key === "+" || e.key === "=") stepPlayRate(1);
    if (e.key === "-" || e.key === "_") stepPlayRate(-1);
  });

  slider.addEventListener("input", (e) => {
    stopPlayback();
    goToEpoch(Number(e.target.value));
  });

  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    if (e.key === "Escape") {
      if (isVideoModalOpen) {
        closeVideoModal();
      } else if (!compareModalBackdrop.classList.contains("is-closed")) {
        closeCompareModal();
      } else if (isModalOpen) {
        closeAnimationModal();
      } else if (selectedTarget) {
        returnToGalaxyView(true);
      }
      return;
    }
    if (e.key === "r" || e.key === "R") {
      camResetBtn.click();
      return;
    }
    if (!frames.length || isModalOpen) return;
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      stopPlayback();
      goToEpoch(currentIndex - 1);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      stopPlayback();
      goToEpoch(currentIndex + 1);
    } else if (e.key === " ") {
      e.preventDefault();
      togglePlayback();
    }
  });

  window.addEventListener("spherex:coordinatesChanged", (e) => {
    stopPlayback();
    clearVideo();
    views = [];
    groupPicker?.classList.add("is-hidden");
    groupAlertEl?.classList.add("is-hidden");
    const label = e.detail?.label ? ` for ${e.detail.label}` : "";
    bodyEl.classList.add("tl-hidden");
    statusEl.className = "timeline-status loading";
    statusEl.textContent = `Querying SPHEREx multi-epoch cutouts${label} via observationsApi.js…`;
    statusEl.classList.remove("tl-hidden");
  });

  // --- Vues : « tous les groupes » (par défaut : il faut parfois tous les groupes pour la
  // vraie trajectoire) ou un seul groupe (même détecteur, λ à ±3 %) choisi par l'utilisateur.
  let views = [];
  let lastAlert = null;

  function groupInfoText(view) {
    if (!view || view.id === "all") {
      return "Toutes les images, tous détecteurs et longueurs d'onde : trajectoire complète.";
    }
    const i = view.info || {};
    const parts = [`${i.n_images} image(s), ${i.n_passages} passage(s)`];
    if (i.mu_arcsec_yr != null && i.n_passages >= 2) {
      parts.push(`mouvement mesuré sur ce groupe seul : ${i.mu_arcsec_yr.toFixed(2)}″/an` +
        (i.mu_err_arcsec_yr != null ? ` ± ${i.mu_err_arcsec_yr.toFixed(2)}` : "") +
        (i.position_angle_deg != null ? `, direction ${Math.round(i.position_angle_deg)}° (0 = nord, 90 = est)` : ""));
    } else {
      parts.push("un seul passage : pas de mouvement mesurable sur ce groupe seul");
    }
    if (i.in_disagreement) parts.push("⚠ en désaccord avec d'autres groupes à un même instant");
    return parts.join(" · ");
  }

  function showView(view) {
    stopPlayback();
    frames = Array.isArray(view?.frames) ? view.frames : [];
    const vid = view?.video;
    if (cutoutVideo && vid?.mp4 && frames.some((f) => typeof f.videoTime === "number")) {
      videoMode = true;
      videoInfo = vid;
      if (cutoutImg) cutoutImg.removeAttribute("src");
      if (cutoutVideo.getAttribute("src") !== vid.mp4) cutoutVideo.src = vid.mp4;
      cutoutVideo.defaultPlaybackRate = playRate;
      cutoutVideo.playbackRate = playRate;
    } else {
      clearVideo();
    }
    if (groupInfoEl) groupInfoEl.textContent = groupInfoText(view);
    if (frames[0]?.fov && cutoutFovLabel) {
      cutoutFovLabel.textContent = `FOV ${frames[0].fov} • WCS-ICRS`;   // taille réellement utilisée
    }
    if (!frames.length) {
      bodyEl.classList.add("tl-hidden");
      statusEl.className = "timeline-status";
      // le backend explique pourquoi (objet non détecté, images indisponibles…)
      statusEl.textContent = lastAlert
        ? `${lastAlert.title} — ${lastAlert.message}`
        : "Aucune image SPHEREx exploitable pour cette position.";
      statusEl.classList.remove("tl-hidden");
      return;
    }
    statusEl.classList.add("tl-hidden");
    bodyEl.classList.remove("tl-hidden");
    slider.max = String(frames.length - 1);
    prevBtn.disabled = nextBtn.disabled = playBtn.disabled = pauseBtn.disabled = frames.length <= 1;
    currentIndex = 0;
    renderDots();
    goToEpoch(0);
  }

  // Cartes cliquables « Groupe affiché » : nom, longueur d'onde, passages, dates, mouvement.
  const MOIS_COURT = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.",
                      "oct.", "nov.", "déc."];
  const moisAn = (iso) => (iso && iso.length >= 7
    ? `${MOIS_COURT[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}` : "");
  const num = (x, nd = 2) => x.toFixed(nd).replace(".", ",");

  function cardContent(v) {
    if (v.id === "all") {
      return {
        title: "Tous les groupes",
        sub: `Trajectoire complète · ${v.frames.length} image(s)`,
        badge: "",
      };
    }
    const i = v.info || {};
    const wl = i.wavelength_um != null ? `${num(i.wavelength_um)} µm` : "";
    const name = i.number || "Groupe";   // G1, G2… (« D » = détecteur)
    const mu = i.mu_arcsec_yr != null && i.n_passages >= 2
      ? `${num(i.mu_arcsec_yr, 1)}${i.mu_err_arcsec_yr != null ? ` ± ${num(i.mu_err_arcsec_yr, 1)}` : ""}″/an`
      : "";
    return {
      title: name,
      sub: `Détecteur ${i.detector || "?"}${wl ? ` · ${wl}` : ""} · ${i.n_passages} passage(s) · ` +
           `${moisAn(i.date_start)} → ${moisAn(i.date_end)}`,
      badge: mu,
      warn: !!i.in_disagreement,
    };
  }

  // Barre de groupes qui défile : flèches ‹ ›, compteur « 2 / 5 », molette = défilement horizontal
  const groupPrevBtn = document.getElementById("group-prev");
  const groupNextBtn = document.getElementById("group-next");
  const groupCountEl = document.getElementById("group-count");
  let currentViewIdx = 0;

  function updateGroupNav() {
    if (groupCountEl) groupCountEl.textContent = `${currentViewIdx + 1} / ${Math.max(views.length, 1)}`;
    if (groupPrevBtn) groupPrevBtn.disabled = currentViewIdx <= 0;
    if (groupNextBtn) groupNextBtn.disabled = currentViewIdx >= views.length - 1;
  }

  function revealCard(idx, smooth = true) {
    const card = groupCardsEl?.children[idx];
    if (!card || !groupCardsEl) return;
    // centre la carte choisie dans la barre (sans faire défiler toute la page)
    const bar = groupCardsEl.getBoundingClientRect();
    const r = card.getBoundingClientRect();
    const left = groupCardsEl.scrollLeft + (r.left - bar.left) - (bar.width - r.width) / 2;
    groupCardsEl.scrollTo({ left: Math.max(0, left), behavior: smooth ? "smooth" : "auto" });
  }

  function selectView(idx) {
    const v = views[idx];
    if (!v) return;
    currentViewIdx = idx;
    if (groupSelect) groupSelect.value = String(idx);
    groupCardsEl?.querySelectorAll(".group-card").forEach((c, j) => {
      c.classList.toggle("active", j === idx);
      c.setAttribute("aria-selected", String(j === idx));
    });
    updateGroupNav();
    revealCard(idx);
    showView(v);
  }

  groupPrevBtn?.addEventListener("click", () => selectView(currentViewIdx - 1));
  groupNextBtn?.addEventListener("click", () => selectView(currentViewIdx + 1));
  // la molette (verticale) fait défiler la barre horizontalement
  groupCardsEl?.addEventListener("wheel", (e) => {
    if (groupCardsEl.scrollWidth <= groupCardsEl.clientWidth) return;
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      groupCardsEl.scrollLeft += e.deltaY;
      e.preventDefault();
    }
  }, { passive: false });
  // flèches du clavier quand la barre a le focus
  groupCardsEl?.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { selectView(Math.min(currentViewIdx + 1, views.length - 1)); e.preventDefault(); }
    if (e.key === "ArrowLeft") { selectView(Math.max(currentViewIdx - 1, 0)); e.preventDefault(); }
  });

  function fillGroupPicker() {
    if (!groupPicker) return;
    if (groupSelect) {
      groupSelect.innerHTML = "";
      views.forEach((v, i) => {
        const opt = document.createElement("option");
        opt.value = String(i);
        groupSelect.appendChild(opt);
      });
    }
    if (groupCardsEl) {
      groupCardsEl.innerHTML = "";
      views.forEach((v, i) => {
        const c = cardContent(v);
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "group-card" + (i === 0 ? " active all" : "") + (c.warn ? " warn" : "");
        btn.setAttribute("role", "option");
        btn.setAttribute("aria-selected", String(i === 0));
        btn.innerHTML =
          `<span class="gc-main"><span class="gc-title"></span><span class="gc-sub"></span></span>` +
          `<span class="gc-badge"></span>`;
        btn.querySelector(".gc-title").textContent = (c.warn ? "⚠ " : "") + c.title;
        btn.querySelector(".gc-sub").textContent = c.sub;
        btn.querySelector(".gc-badge").textContent = c.badge;
        btn.addEventListener("click", () => selectView(i));
        groupCardsEl.appendChild(btn);
      });
    }
    groupPicker.classList.toggle("is-hidden", views.length <= 1);
    currentViewIdx = 0;
    updateGroupNav();
    if (groupCardsEl) groupCardsEl.scrollLeft = 0;
  }

  groupSelect?.addEventListener("change", () => selectView(Number(groupSelect.value)));

  function showGroupAlert(alert) {
    if (!groupAlertEl) return;
    // affiché seulement quand il y a quelque chose à savoir (pas pour « tout concorde »)
    if (!alert || alert.level === "ok") {
      groupAlertEl.classList.add("is-hidden");
      return;
    }
    groupAlertEl.className = `group-alert ${alert.level}`;
    groupAlertEl.querySelector(".ga-title").textContent =
      (alert.level === "warn" ? "⚠ " : "ℹ ") + alert.title;
    groupAlertEl.querySelector(".ga-msg").textContent = alert.message;
  }

  // --- Fenêtre « Vidéo SPHEREx » (clic sur l'objet) : on y DÉPLACE la vidéo, la frise,
  // le choix du groupe et le message ; à la fermeture, ils reviennent à leur place.
  // Mêmes éléments -> même état (date, vitesse, groupe, lecture).
  const videoModalBackdrop = document.getElementById("video-modal-backdrop");
  const videoModalMain = document.getElementById("video-modal-main");
  const videoModalSide = document.getElementById("video-modal-side");
  const videoModalTitle = document.getElementById("video-modal-title");
  const closeVideoModalBtn = document.getElementById("close-video-modal");
  let isVideoModalOpen = false;
  let movedBack = [];

  function moveKeepingPlayback(moves) {
    const wasPlaying = videoMode && cutoutVideo && !cutoutVideo.paused && !cutoutVideo.ended;
    const t = cutoutVideo ? cutoutVideo.currentTime : 0;
    moves();
    if (cutoutVideo && videoMode) {
      if (Math.abs(cutoutVideo.currentTime - t) > 0.05) cutoutVideo.currentTime = t;
      if (wasPlaying) cutoutVideo.play().catch(() => {});
    }
    requestAnimationFrame(drawMarkers);
  }

  function openVideoModal(target) {
    if (!videoModalBackdrop) return;
    if (target && selectedTarget?.id !== target.id) selectAndZoomToTarget(target);
    const t = target || selectedTarget;
    if (videoModalTitle) {
      videoModalTitle.textContent = `${t?.shortName || t?.name || "Cible"} — vidéo SPHEREx`;
    }
    if (isVideoModalOpen) return;
    const stage = document.querySelector(".cutout-media-stage");
    const dock = document.getElementById("timeline-dock");
    const parts = [
      [stage, videoModalMain],
      [dock, videoModalMain],
      [groupPicker, videoModalSide],
      [epochNoteEl, videoModalSide],
      [groupAlertEl, videoModalSide],
    ].filter(([el]) => el);
    moveKeepingPlayback(() => {
      movedBack = parts.map(([el, dest]) => {
        const ph = document.createComment("place");
        el.before(ph);
        dest.appendChild(el);
        return [el, ph];
      });
    });
    isVideoModalOpen = true;
    videoModalBackdrop.classList.remove("is-closed");
    requestAnimationFrame(() => revealCard(currentViewIdx, false));   // la barre a changé de largeur
  }

  function closeVideoModal() {
    if (!isVideoModalOpen) return;
    moveKeepingPlayback(() => {
      movedBack.forEach(([el, ph]) => ph.replaceWith(el));
      movedBack = [];
    });
    isVideoModalOpen = false;
    videoModalBackdrop.classList.add("is-closed");
    requestAnimationFrame(() => revealCard(currentViewIdx, false));
  }

  closeVideoModalBtn?.addEventListener("click", closeVideoModal);
  videoModalBackdrop?.addEventListener("click", (e) => {
    if (e.target === videoModalBackdrop) closeVideoModal();
  });

  // =========================================================
  // Fraîcheur des données SPHEREx : le serveur revérifie IRSA chaque semaine et intègre
  // les nouvelles images en arrière-plan ; ici on l'affiche et on propose la nouvelle vidéo
  // =========================================================
  const freshEl = document.getElementById("data-freshness");
  const freshText = freshEl?.querySelector(".df-text");
  const toastEl = document.getElementById("data-update-toast");
  const toastText = toastEl?.querySelector(".dut-text");
  const toastShowBtn = document.getElementById("data-update-show");
  let shownData = null;          // résultat affiché : { key, computedAt, targetId, label }
  let freshTimer = null;

  const frDay = (iso) => {
    if (!iso) return "—";
    const d = new Date(iso.length <= 10 ? `${iso}T00:00:00Z` : iso);
    return Number.isNaN(d.getTime())
      ? iso
      : d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
  };

  function sinceText(iso) {
    const t = iso ? Date.parse(iso) : NaN;
    if (Number.isNaN(t)) return "";
    const h = (Date.now() - t) / 3.6e6;
    if (h < 1) return "à l'instant";
    if (h < 24) return `il y a ${Math.round(h)} h`;
    const d = Math.round(h / 24);
    return d === 1 ? "hier" : `il y a ${d} jours`;
  }

  function renderFreshness(u) {
    if (!freshEl || !freshText) return;
    if (!u) {
      freshEl.classList.add("is-hidden");
      return;
    }
    const st = u.status;
    const imgs = u.n_images_found != null
      ? `${u.n_images_found} images SPHEREx` +
        (u.last_image_date ? ` · la plus récente : ${frDay(u.last_image_date)}` : "")
      : "";
    let text;
    if (st === "updating") {
      text = "Recherche de nouvelles images SPHEREx sur IRSA… (la vidéo actuelle reste affichée)";
    } else {
      const out = u.last_outcome?.outcome;
      const checked = out === "no-new-images" && sinceText(u.checked_at) === "à l'instant"
        ? "vérifié à l'instant : aucune nouvelle image"
        : `vérifié ${sinceText(u.checked_at)}`;
      const next = st === "off"
        ? "mise à jour automatique désactivée"
        : u.next_check_at
          ? `prochaine vérification : ${frDay(u.next_check_at)}`
          : "";
      text = [imgs, checked, next].filter(Boolean).join(" · ");
      if (out === "irsa-unavailable") text += " · IRSA indisponible, nouvel essai plus tard";
    }
    freshText.textContent = text;
    freshEl.classList.toggle("updating", st === "updating");
    freshEl.classList.remove("is-hidden");
  }

  function scheduleFreshPoll(ms) {
    clearTimeout(freshTimer);
    freshTimer = setTimeout(pollUpdates, ms);
  }

  async function pollUpdates() {
    let next = 5 * 60 * 1000;                    // toutes les 5 min
    try {
      if (shownData?.key && window.ObservationsApi?.fetchUpdateStatus && !document.hidden) {
        const st = await window.ObservationsApi.fetchUpdateStatus();
        const row = (st.results || []).find((r) => r.key === shownData.key);
        if (row) {
          if (row.status === "updating") next = 20 * 1000;   // suivi rapproché pendant la recherche
          if (row.computed_at && shownData.computedAt && row.computed_at !== shownData.computedAt) {
            const n = row.last_outcome?.new_images;
            toastText.textContent =
              `Nouvelles images SPHEREx pour ${shownData.label}` + (n ? ` (+${n})` : "") +
              " : la vidéo a été mise à jour.";
            toastEl.classList.remove("is-hidden");
          }
          renderFreshness(row);
        }
      }
    } catch (_) {
      /* serveur momentanément injoignable : on réessaiera */
    }
    scheduleFreshPoll(next);
  }

  toastShowBtn?.addEventListener("click", () => {
    toastEl.classList.add("is-hidden");
    if (selectedTarget && selectedTarget.id === shownData?.targetId) loadObservations(selectedTarget);
  });

  window.addEventListener("spherex:framesLoaded", (e) => {
    const u = e.detail?.update || null;
    shownData = e.detail?.resultKey
      ? {
          key: e.detail.resultKey,
          computedAt: u?.computed_at || null,
          targetId: e.detail.targetId,
          label: selectedTarget?.shortName || selectedTarget?.name || "cette cible",
        }
      : null;
    toastEl?.classList.add("is-hidden");
    renderFreshness(u);
    scheduleFreshPoll(u?.status === "updating" ? 15 * 1000 : 5 * 60 * 1000);
  });

  window.addEventListener("spherex:framesLoaded", (e) => {
    lastAlert = e.detail?.alert || null;
    showGroupAlert(e.detail?.alert);
    const given = Array.isArray(e.detail?.views) ? e.detail.views : [];
    views = given.length
      ? given
      : [{ id: "all", frames: e.detail?.frames || [], video: e.detail?.video || null }];
    fillGroupPicker();
    showView(views[0]);                  // par défaut : tous les groupes
  });

  window.addEventListener("spherex:framesError", (e) => {
    stopPlayback();
    clearVideo();
    bodyEl.classList.add("tl-hidden");
    statusEl.className = "timeline-status error";
    statusEl.textContent = e.detail?.message || "Failed to load observations.";
    statusEl.classList.remove("tl-hidden");
  });

  // =========================================================
  // 17. Initial Render & Deep-Link Boot
  // =========================================================
  build3DStarfield();
  renderGalaxySwitcher();
  renderSideList();
  syncCamControlsUI();

  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      build3DStarfield();
    }, 100);
  });

  requestAnimationFrame(renderFrame);

  try {
    const params = new URLSearchParams(window.location.search);
    const initRa = params.get("ra");
    const initDec = params.get("dec");
    if (initRa === null || initDec === null) startIntro();
    if (initRa !== null && initDec !== null) {
      raInput.value = initRa;
      decInput.value = initDec;
      form.dispatchEvent(new Event("submit"));
    }
  } catch (_) {}
});
