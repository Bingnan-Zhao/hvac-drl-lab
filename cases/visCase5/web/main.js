// Case 05 live viewer: the Blender model (assets/hvac.glb) driven by the FMU state streamed from backend/server.py.
// Blender coordinates (x east, y north, z up) arrive in glTF as three.js (x, z, -y); B() converts.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const WS_URL = `ws://${location.hostname || '127.0.0.1'}:8766`;
const ZONES = ['Eas', 'Wes', 'Int'];
const ZNAME = { Eas: 'East zone', Wes: 'West zone', Int: 'Interior zone' };
const NOM = { box: [0.43, 0.43, 0.33], sup: 1.1, oa: 0.26, chw: 1.05, qcoi: 22e3, reh: [2.2e3, 2.2e3, 1.5e3] };
const B = (x, y, z) => new THREE.Vector3(x, z, -y);
const f1 = (v, n = 1) => (v ?? NaN).toFixed(n);
const clamp01 = x => Math.min(1, Math.max(0, x));

// ------------------------------------------------------------------ renderer and scene
const view = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.85;
renderer.localClippingEnabled = true;
view.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x15181d);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.35;
const camera = new THREE.PerspectiveCamera(38, innerWidth / innerHeight, 0.05, 300);
camera.position.copy(B(-5, -7, 16));
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(B(9, 9, 0.8));
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.495;

scene.add(new THREE.HemisphereLight(0xe6eeff, 0x2a2d33, 0.35));
const sun = new THREE.DirectionalLight(0xfff4e6, 1.7);
sun.position.copy(B(-6, -10, 22)); sun.target.position.copy(B(9, 8, 0)); scene.add(sun.target);
sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 70 });
scene.add(sun);
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

// ------------------------------------------------------------------ colour map (12-30 degC), CFD-style
const STOPS = [[0, 0x30123b], [0.12, 0x4145ab], [0.25, 0x4675ed], [0.37, 0x39a2fc], [0.5, 0x1bcfd4], [0.62, 0x24eca6],
  [0.72, 0x61fc6c], [0.8, 0xa4fc3b], [0.87, 0xd1e834], [0.93, 0xf3c63a], [1, 0xfe9b2d]];
// air scale: 'system' auto-ranges over supply/mixed/discharge/room air, 'rooms' zooms onto the room air,
// 'fixed' is 12-30 degC; chilled water always uses its own 5-15 degC scale
let TMIN = 12, TMAX = 30;
const WMIN = 5, WMAX = 15;
const _c = new THREE.Color();
function tempColor(T, out = new THREE.Color(), lo = TMIN, hi = TMAX) {
  const x = clamp01((T - lo) / (hi - lo));
  for (let i = 1; i < STOPS.length; i++) {
    if (x <= STOPS[i][0]) {
      const f = (x - STOPS[i - 1][0]) / (STOPS[i][0] - STOPS[i - 1][0]);
      return out.set(STOPS[i - 1][1]).lerp(_c.set(STOPS[i][1]), f);
    }
  }
  return out.set(STOPS.at(-1)[1]);
}
const waterColor = (T, out) => tempColor(T, out, WMIN, WMAX);
(function drawBar() {
  const c = document.getElementById('cbar'), g = c.getContext('2d');
  for (let i = 0; i < c.width; i++) {
    g.fillStyle = '#' + tempColor(i / c.width, undefined, 0, 1).getHexString();
    g.fillRect(i, 0, 1, c.height);
  }
})();
function updateScale(f) {
  // fixed scales by default: an auto range would recolour every zone whenever one zone changes
  const mode = document.getElementById('cscale').value;
  let lo = 18, hi = 28;
  if (mode === 'system') { lo = 10; hi = 30; }
  if (mode === 'auto') {
    const vals = f.zones.map(q => q.TZon);
    lo = Math.floor(Math.min(...vals) - 1); hi = Math.ceil(Math.max(...vals) + 1);
    if (hi - lo < 4) { const m = (lo + hi) / 2; lo = m - 2; hi = m + 2; }
  }
  TMIN = lo; TMAX = hi;
  const t = document.querySelectorAll('#legend .ticks span');
  [0, 1 / 3, 2 / 3, 1].forEach((x, k) => (t[k].textContent = f1(TMIN + (TMAX - TMIN) * x, 1) + (k === 3 ? ' °C' : '')));
}

// ------------------------------------------------------------------ part definitions
// Each part: name, regex over node names, tooltip text, thermal temperature (or null), explode lift.
const zi = z => ZONES.indexOf(z);
const meanTZon = f => f.zones.reduce((s, q) => s + q.TZon * q.mRet, 0) / Math.max(1e-6, f.zones.reduce((s, q) => s + q.mRet, 0)) || f.zones[0].TZon;
const DEFS = [
  ['ahu_damper_oa', /^ahu_damper_oa/, f => `Outdoor air damper\n${f1(f.ahu.mOA, 2)} kg/s at ${f1(f.w.TOut)} °C, RH ${f1(100 * f.w.phiOut, 0)} %`, f => f.w.TOut, 0.4],
  ['ahu_damper_ret', /^ahu_damper_ret/, f => `Return air damper\n${f1(f.ahu.mSup - f.ahu.mOA, 2)} kg/s at ${f1(meanTZon(f))} °C`, f => meanTZon(f), 0.6],
  ['ahu_damper_rel', /^ahu_damper_rel|^ahu_mix_relief/, f => `Relief damper\n${f1(f.ahu.mRel, 2)} kg/s to outdoors`, f => f.ahu.TMix, 0.4],
  ['ahu_mix', /^ahu_mix/, f => `Mixing box\nMixed air ${f1(f.ahu.TMix)} °C\nOutdoor air fraction ${f1(100 * f.ahu.mOA / Math.max(1e-6, f.ahu.mSup), 0)} %`, f => f.ahu.TMix, 0.2],
  ['ahu_filter', /^ahu_filter/, f => `Filter bank (pleated, 2 x 2)\nAir ${f1(f.ahu.TMix)} °C`, f => f.ahu.TMix, 0.2],
  ['ahu_fan', /^ahu_fan/, f => `Supply fan (plug fan, VSD)\n${f1(f.ahu.mSup, 2)} kg/s, ${f1(f.ahu.dpFan, 0)} Pa\nElectric power ${f1(f.P.fan / 1000, 2)} kW`, f => f.ahu.TMix, 0.2],
  ['ahu_coil', /^ahu_coil/, f => `Chilled-water cooling coil\n${f1(f.ahu.QCoi / 1000, 1)} kW, CHW ${f1(f.ahu.mCHW, 2)} kg/s\nWater ${f1(f.ahu.TCHWSup, 1)} → ${f1(f.ahu.TCHWRet, 1)} °C\nAir leaving ${f1(f.ahu.TSup)} °C (set ${f1(f.ahu.TSupSet)} °C)`, f => f.ahu.TSup, 0.2],
  ['ahu_dis', /^ahu_dis/, f => `Discharge plenum\nSupply air ${f1(f.ahu.TSup)} °C, ${f1(f.ahu.mSup, 2)} kg/s`, f => f.ahu.TSup, 0.2],
  ['ahu_controls', /^ahu_control/, f => `AHU controller\nSupply air set point ${f1(f.ahu.TSupSet)} °C (${f.cfg.mode.toUpperCase()})`, null, 0.2],
  ['ahu_frame', /^ahu/, () => 'AHU base frame', null, 0],
  ['chiller', /^chiller/, f => `Air-cooled chiller (COP 4.5)\nCooling ${f1(f.ahu.QCoi / 1000, 1)} kW\nElectric ${f1(f.P.coo / 1000, 2)} kW`, null, 0.3],
  ['chw_pump', /^chw_pump/, f => `Chilled-water pump\n${f1(f.ahu.mCHW, 2)} kg/s`, null, 0.3],
  ['chw_valve', /^chw_control_valve/, f => `Coil control valve\n${f1(100 * f.ahu.mCHW / NOM.chw, 0)} % of design flow`, null, 0.3],
  ['chw_supply', /^chw_supply/, f => `Chilled water supply\n${f1(f.ahu.TCHWSup, 1)} °C, ${f1(f.ahu.mCHW, 2)} kg/s`, f => f.ahu.TCHWSup, 0.3],
  ['chw_return', /^chw_return/, f => `Chilled water return\n${f1(f.ahu.TCHWRet, 1)} °C`, f => f.ahu.TCHWRet, 0.3],
  ['chw_fittings', /^chw/, () => 'Valves, strainer, supports', null, 0.3],
  ['duct_supply_main', /^duct_supply_(main|tee|riser|elbow|link|offset)/, f => `Supply main duct (500 x 300)\n${f1(f.ahu.mSup, 2)} kg/s at ${f1(f.ahu.TSup)} °C`, f => f.ahu.TSup, 1.6],
  ...ZONES.map(z => [`duct_branch_${z}`, new RegExp(`^duct_(supply_${{ Eas: 'east', Wes: 'west', Int: 'interior' }[z]}|reducer_${z}|round_${z})`),
    f => `Branch duct to ${ZNAME[z].toLowerCase()} box\n${f1(f.zones[zi(z)].mBox, 2)} kg/s at ${f1(f.ahu.TSup)} °C`, f => f.ahu.TSup, 1.8]),
  ...ZONES.map(z => [`vav_${z}`, new RegExp(`^vav_${z}`), f => {
    const q = f.zones[zi(z)];
    return `VAV box, ${ZNAME[z].toLowerCase()}\nDamper ${f1(100 * q.yDam, 0)} % open → ${f1(q.mBox, 2)} kg/s\nElectric reheat ${f1(q.QReh / 1000, 2)} kW\nDischarge air ${f1(q.TDis)} °C`;
  }, f => f.zones[zi(z)].TDis, 2.2]),
  ...ZONES.map(z => [`flex_${z}`, new RegExp(`^(flexduct|duct_plenum)_${z}`), f => `Flexible ducts, ${ZNAME[z].toLowerCase()}\n${f1(f.zones[zi(z)].mBox, 2)} kg/s at ${f1(f.zones[zi(z)].TDis)} °C`, f => f.zones[zi(z)].TDis, 1.4]),
  ...ZONES.map(z => [`diffusers_${z}`, new RegExp(`^(diffuser|plume)_${z}`), f => `Ceiling diffusers, ${ZNAME[z].toLowerCase()}\n${f1(f.zones[zi(z)].mBox, 2)} kg/s at ${f1(f.zones[zi(z)].TDis)} °C`, f => f.zones[zi(z)].TDis, 0.9]),
  ...ZONES.map(z => [`grilles_${z}`, new RegExp(`^return_grille_${z}`), f => `Return grilles, ${ZNAME[z].toLowerCase()}\n${f1(f.zones[zi(z)].mRet, 2)} kg/s at ${f1(f.zones[zi(z)].TZon)} °C`, f => f.zones[zi(z)].TZon, 0.9]),
  ['duct_return', /^duct_return/, f => `Return duct (from ceiling plenum)\n${f1(f.zones.reduce((s, q) => s + q.mRet, 0), 2)} kg/s at ${f1(meanTZon(f))} °C`, f => meanTZon(f), 1.6],
  ...ZONES.map(z => [`zone_${z}`, new RegExp(`^(building_floor|air)_${z}`), f => {
    const q = f.zones[zi(z)];
    return `${ZNAME[z]}\nAir ${f1(q.TZon)} °C   RH ${f1(100 * q.phi, 0)} %\nSet points ${f1(f.cfg.THeaSet[zi(z)])}–${f1(f.cfg.TCooSet[zi(z)])} °C\nCooling loop ${f1(100 * q.yCoo, 0)} %   heating loop ${f1(100 * q.yReh, 0)} %`;
  }, f => f.zones[zi(z)].TZon, 0]),
  ...ZONES.map(z => [`people_${z}`, new RegExp(`^person_${z}`), f => `Occupants, ${ZNAME[z].toLowerCase()}\nInternal gains × ${f1(f.cfg.fGai[zi(z)])}`, null, 0]),
  ['furniture', /^furn/, () => 'Workstations', null, 0],
  ['ceiling', /^ceiling/, () => 'Suspended ceiling (600 mm tiles) with LED troffers', null, 3.0],
  ['building', /^(building|plant)/, f => `Building envelope\nOutdoor ${f1(f.w.TOut)} °C, solar ${f1(f.w.HGlo, 0)} W/m²`, null, 0],
];
// selection at equipment level groups several parts
const EQUIP = [
  ['Air handling unit', /^ahu/], ['Air-cooled chiller', /^chiller$/], ['Chilled-water loop', /^chw/],
  ...ZONES.map(z => [`Terminal unit, ${ZNAME[z].toLowerCase()}`, new RegExp(`^(vav|duct_branch|flex|diffusers|grilles)_${z}$`)]),
  ['Main supply and return ducts', /^duct_(supply_main|return)$/],
  ['Office floor', /^(zone|people|furniture|building|ceiling)/],
];
const GHOST_PARTS = /^(building|furniture|people|ceiling|zone)/;

// ------------------------------------------------------------------ load the model and build parts
const parts = [], byName = {}, pickables = [];
const root = new THREE.Group(); scene.add(root);
const nodes = {};   // name -> Object3D, for animated pieces
let ready = false;

const neutralSolid = new THREE.MeshStandardMaterial({ color: 0x7d838b, roughness: 0.75, metalness: 0.1 });
const neutralGhost = new THREE.MeshStandardMaterial({ color: 0x9aa1aa, roughness: 0.9, transparent: true, opacity: 0.08, depthWrite: false });

function makePart([name, re, info, temp, lift]) {
  const g = new THREE.Group(); g.name = 'part:' + name; root.add(g);
  const p = { name, re, info, temp, lift, group: g, dir: new THREE.Vector3(), meshes: [], matCache: new Map(),
    thermal: new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.55, metalness: 0.05, emissive: 0x000000 }) };
  parts.push(p); byName[name] = p;
  return p;
}
DEFS.forEach(makePart);

function partFor(name) { return parts.find(p => p.re.test(name)); }

// thermal overlays built here: translucent room air volumes and diffuser plumes
const ZX = { Wes: [0, 4], Int: [4, 14], Eas: [14, 18] };
const airMats = {}, plumeMats = {};
function addOverlays(model) {
  for (const z of ZONES) {
    const [x0, x1] = ZX[z];
    const m = new THREE.MeshStandardMaterial({ color: 0x1bcfd4, transparent: true, opacity: 0.22, depthWrite: false, roughness: 1, metalness: 0, side: THREE.DoubleSide });
    airMats[z] = m;
    const air = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0 - 0.06, 2.74, 11.94), m);
    air.position.copy(B((x0 + x1) / 2, 6, 1.4)); air.name = `air_${z}`; air.userData.overlay = true;
    model.add(air);
    const pm = new THREE.MeshBasicMaterial({ color: 0x4675ed, transparent: true, opacity: 0.3, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
    plumeMats[z] = pm;
    model.traverse(o => {
      const mm = /^diffuser_(\w+)_(\d+)$/.exec(o.name);
      if (!mm || mm[1] !== z) return;
      const c = new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());
      // four-way throw: a flattened cone hugging the ceiling plus a falling core
      const cone = new THREE.Mesh(new THREE.ConeGeometry(0.95, 0.8, 32, 1, true), pm);
      cone.position.set(c.x, 2.8 - 0.4, c.z); cone.name = `plume_${z}_${mm[2]}`; cone.userData.overlay = true;
      model.add(cone);
    });
  }
}

// the stand-alone demo embeds the model (window.__GLB_BUFFER); the live viewer loads the file
function loadModel(onLoad, onProgress, onError) {
  const loader = new GLTFLoader();
  if (window.__GLB_BUFFER) loader.parse(window.__GLB_BUFFER, '', onLoad, onError);
  else loader.load('assets/hvac.glb', onLoad, onProgress, onError);
}
loadModel(gltf => {
  const model = gltf.scene;
  addOverlays(model);
  model.updateMatrixWorld(true);
  // collect animated nodes before reparenting
  model.traverse(o => { if (o.name) nodes[o.name] = o; });
  // assign each node to a part: a node whose part differs from its parent's part moves to that part's group
  const list = [];
  model.traverse(o => list.push(o));
  const owner = new Map();
  for (const o of list) {
    if (o === model) continue;
    const own = partFor(o.name) || owner.get(o.parent) || null;
    owner.set(o, own);
    if (own && own !== owner.get(o.parent)) own.group.attach(o);
  }
  for (const o of list) {
    if (!o.isMesh) continue;
    const p = owner.get(o);
    if (!p) continue;
    // per-part material copies so x-ray, highlight and thermal colouring stay local to a part
    const src = o.material;
    if (!p.matCache.has(src)) {
      const m = src.clone();
      if (src.transparent || src.opacity < 1) { m.depthWrite = false; }
      p.matCache.set(src, m);
    }
    o.material = o.userData.realMat = p.matCache.get(src);
    o.castShadow = !o.material.transparent && !o.userData.overlay;
    o.receiveShadow = !o.userData.overlay;
    o.userData.part = p;
    p.meshes.push(o);
    if (!o.userData.overlay || /^air_/.test(o.name)) pickables.push(o);
  }
  // explode directions: away from the plant/floor centre, ducts lifted
  const centre = B(9, 9, 1.5);
  for (const p of parts) {
    if (!p.meshes.length) continue;
    const c = new THREE.Box3().setFromObject(p.group).getCenter(new THREE.Vector3());
    p.dir.subVectors(c, centre).multiplyScalar(0.35).setY(p.lift);
    if (/^(building|furniture|zone|people)/.test(p.name)) p.dir.set(0, 0, 0);
  }
  buildExplodeTree();
  // heater elements: one emissive material per zone
  for (const z of ZONES) {
    const m = nodes[`vav_${z}_heater_element_0`].material.clone();
    m.emissive = new THREE.Color(0xff5a14); m.emissiveIntensity = 0;
    heaterMats[z] = m;
    for (let k = 0; k < 3; k++) { const o = nodes[`vav_${z}_heater_element_${k}`]; o.material = o.userData.realMat = m; }
  }
  for (const n of ['building_slab_above']) if (nodes[n]) nodes[n].visible = false;
  // the wall between the office and the plant deck is drawn translucent so the plant stays visible
  const wn = nodes['building_wall_north'];
  if (wn) { wn.material = wn.userData.realMat = wn.material.clone(); Object.assign(wn.material, { transparent: true, opacity: 0.18, depthWrite: false }); wn.castShadow = false; { const k = pickables.indexOf(wn); if (k >= 0) pickables.splice(k, 1); } }
  buildFlowPaths();
  setDisplay('real');
  ready = true;
  document.getElementById('status').textContent = ws && ws.readyState === 1 ? 'connected' : document.getElementById('status').textContent;
}, ev => {
  if (ev.total) document.getElementById('status').textContent = `loading model ${Math.round(100 * ev.loaded / ev.total)} %`;
}, err => { document.getElementById('status').textContent = 'model failed to load: ' + err.message; });
const heaterMats = {};

// ------------------------------------------------------------------ exploded view of a selection
// Every part is split into items: empties (sub-assemblies, e.g. the fan impeller) and clusters of meshes that share a
// name stem (e.g. all coil fins). Each item moves away from the centre of its parent level, recursively, so a selected
// unit comes apart down to its fan, motor, shaft, blades, dampers and panels.
const stem = n => n.replace(/(_[0-9]+)+$/, '');
function boxCentre(objs) {
  const b = new THREE.Box3();
  for (const o of objs) b.expandByObject(o);
  return b.isEmpty() ? null : b.getCenter(new THREE.Vector3());
}
function makeItems(node) {
  const items = [], clusters = new Map();
  for (const ch of node.children) {
    if (ch.isPoints || ch.userData.overlay) continue;
    if (ch.type === 'Object3D') items.push({ objs: [ch], sub: makeItems(ch) });
    else {
      const k = stem(ch.name);
      if (!clusters.has(k)) { const it = { objs: [], sub: [] }; clusters.set(k, it); items.push(it); }
      clusters.get(k).objs.push(ch);
    }
  }
  return items;
}
function measure(items) {
  for (const it of items) {
    it.c = boxCentre(it.objs);
    for (const o of it.objs) { o.userData.p0 = o.position.clone(); o.userData.off = new THREE.Vector3(); }
    measure(it.sub);
  }
}
function buildExplodeTree() {
  for (const p of parts) {
    p.items = makeItems(p.group);
    measure(p.items);
    p.c0 = boxCentre([p.group]);
  }
}
const _d = new THREE.Vector3();
function spread(items, centre, e, depth) {
  for (const it of items) {
    if (!it.c) continue;
    _d.subVectors(it.c, centre);
    const len = _d.length();
    const off = len > 0.03 ? _d.clone().multiplyScalar(1.3 * e).addScaledVector(_d.normalize(), (0.3 / (1 + 0.5 * depth)) * e) : new THREE.Vector3();
    for (const o of it.objs) o.userData.off.copy(off);
    spread(it.sub, it.c, e, depth + 1);
  }
}
function clearItems(items) {
  for (const it of items) { for (const o of it.objs) o.userData.off.set(0, 0, 0); clearItems(it.sub); }
}
function placeItems(items) {
  for (const it of items) {
    for (const o of it.objs) {
      o.position.copy(o.userData.p0).add(o.userData.off);
      if (o.userData.animOff) o.position.add(o.userData.animOff);
    }
    placeItems(it.sub);
  }
}

// ------------------------------------------------------------------ display modes: realistic / thermal
let display = 'real';
function setDisplay(mode) {
  display = mode;
  document.querySelectorAll('#display button').forEach(b => b.classList.toggle('on', b.dataset.v === mode));
  for (const p of parts) for (const o of p.meshes) {
    if (o.userData.overlay) { o.visible = mode === 'thermal' && (/^air_/.test(o.name) ? document.getElementById('roomAir').checked : true); continue; }
    if (mode === 'real') o.material = o.userData.realMat;
    else if (p.temp && !/^(furn|person|building_(?!floor))/.test(o.name)) o.material = p.thermal;
    else o.material = GHOST_PARTS.test(p.name) && !/^building_floor/.test(o.name) ? neutralGhost : neutralSolid;
  }
  applyXray();
}
document.querySelectorAll('#display button').forEach(b => (b.onclick = () => setDisplay(b.dataset.v)));
document.getElementById('roomAir').onchange = () => setDisplay(display);

// ------------------------------------------------------------------ air and water flow particles
const dot = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.85)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
})();
const paths = [];
function flowPath(pts, flow, temp, nominal, size = 0.11, density = 9, water = false) {
  const curve = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.05);
  const len = curve.getLength(), n = Math.max(6, Math.round(len * density));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  const m = new THREE.PointsMaterial({ size, map: dot, color: 0xffffff, transparent: true, opacity: 0.95, depthWrite: false, sizeAttenuation: true });
  const obj = new THREE.Points(geo, m); obj.frustumCulled = false; scene.add(obj);
  const jitter = Array.from({ length: n }, () => new THREE.Vector3((Math.random() - 0.5), (Math.random() - 0.5), (Math.random() - 0.5)).multiplyScalar(size * 1.4));
  paths.push({ water, curve, n, s: Array.from({ length: n }, (_, k) => (k + Math.random() * 0.5) / n), flow, temp, nominal, geo, m, obj, len, jitter });
}
function buildFlowPaths() {
  const DY = 3.3, AY = 14.6, AZ = 0.78;
  const ahuIn = B(4.9, AY, AZ);
  // outdoor air through the louvre hood into the mixing box
  flowPath([B(3.4, AY, 0.5), B(3.95, AY, 0.65), B(4.4, AY, AZ), ahuIn], f => f.ahu.mOA, f => f.w.TOut, NOM.oa);
  // relief air out of the north side of the mixing box
  flowPath([B(4.9, AY + 0.1, 1.1), B(4.9, AY + 0.6, 1.0), B(4.9, AY + 0.9, 1.25), B(4.9, AY + 1.6, 1.5)], f => f.ahu.mRel, f => f.ahu.TMix, NOM.oa);
  // supply: through filter, fan, coil, discharge, riser, main duct to the tee
  flowPath([ahuIn, B(5.65, AY, AZ), B(6.45, AY, AZ), B(7.5, AY, AZ), B(8.3, AY, AZ + 0.2), B(8.4, AY, 1.5), B(8.4, AY, 2.6),
    B(8.4, AY, DY), B(8.4, 13.4, DY), B(8.3, 12.1, DY), B(8.3, 9.0, DY), B(8.3, 6.0, DY)], f => f.ahu.mSup, f => f.ahu.TSup, NOM.sup, 0.12, 8);
  const boxes = {
    Eas: { pts: [B(8.3, 6.0, DY), B(11.0, 6.0, DY), B(13.45, 6.0, DY), B(14.6, 6.0, DY), B(15.4, 6.0, DY)], out: [15.7, 6.0], dir: 'x' },
    Wes: { pts: [B(8.3, 6.0, DY), B(6.0, 6.0, DY), B(4.5, 6.0, DY), B(3.4, 6.0, DY), B(2.6, 6.0, DY)], out: [2.3, 6.0], dir: 'x' },
    Int: { pts: [B(8.3, 6.0, DY), B(8.3, 5.0, DY), B(8.3, 4.2, DY), B(8.3, 3.4, DY), B(8.3, 2.9, DY)], out: [8.3, 2.65], dir: 'y' },
  };
  const DIFF = { Eas: [[16.2, 3.0], [16.2, 9.0]], Wes: [[1.8, 3.0], [1.8, 9.0]], Int: [[6.0, 3.0], [10.6, 3.0], [6.0, 9.0], [10.6, 9.0]] };
  const GRILLE = { Eas: [[16.2, 6.0]], Wes: [[1.8, 6.0]], Int: [[6.0, 6.0], [10.6, 6.0]] };
  for (const z of ZONES) {
    const i = zi(z), b = boxes[z], nd = DIFF[z].length;
    flowPath(b.pts, f => f.zones[i].mBox, f => f.ahu.TSup, NOM.box[i], 0.1, 8);
    for (const [x, y] of DIFF[z]) {
      const [sx, sy] = b.out;
      const route = b.dir === 'x'
        ? [B(sx, sy, DY), B((sx + x) / 2, sy, DY), B(x, sy, DY), B(x, (sy + y) / 2, DY), B(x, y, DY), B(x, y, 3.0), B(x, y, 2.75)]
        : [B(sx, sy, DY), B(sx, sy - 0.3, DY), B(x, sy - 0.3, DY), B(x, y, DY), B(x, y, 3.0), B(x, y, 2.75)];
      flowPath(route, f => f.zones[i].mBox / nd, f => f.zones[i].TDis, NOM.box[i] / nd, 0.09, 8);
      // four-way throw along the ceiling, then falling into the occupied zone
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        flowPath([B(x + 0.25 * dx, y + 0.25 * dy, 2.74), B(x + 1.0 * dx, y + 1.0 * dy, 2.7), B(x + 1.7 * dx, y + 1.7 * dy, 2.2), B(x + 2.0 * dx, y + 2.0 * dy, 1.3)],
          f => f.zones[i].mBox / nd / 4, f => f.zones[i].TDis * 0.6 + f.zones[i].TZon * 0.4, NOM.box[i] / nd / 4, 0.07, 10);
      }
    }
    // room air rising to the return grilles, then through the ceiling plenum to the return duct inlet
    for (const [x, y] of GRILLE[z]) {
      flowPath([B(x + 1.2, y + 1.0, 1.1), B(x + 0.5, y + 0.4, 2.0), B(x, y, 2.78), B(x, y, 3.05), B((x + 5.4) / 2, (y + 11.3) / 2, 3.15), B(5.4, 11.3, DY)],
        f => f.zones[i].mRet / GRILLE[z].length, f => f.zones[i].TZon, NOM.box[i] / GRILLE[z].length, 0.09, 6);
    }
  }
  // return duct to the mixing box (through the north wall, down onto the return damper)
  flowPath([B(5.4, 11.3, DY), B(5.4, 13.0, DY), B(5.4, 13.6, DY), B(5.05, 13.8, DY), B(5.05, AY, DY - 0.1), B(5.05, AY, 2.0), B(5.05, AY, 1.4), B(4.95, AY, 0.95), ahuIn],
    f => f.zones.reduce((s, q) => s + q.mRet, 0), f => meanTZon(f), NOM.sup, 0.12, 8);
  // chilled water: chiller evaporator -> pump -> coil -> back
  const ev = [13.0, 14.55, 0.45];
  flowPath([B(ev[0], ev[1] + 0.15, 0.55), B(ev[0], 15.55, 0.55), B(11.0, 15.55, 0.55), B(10.2, 15.55, 0.55), B(9.0, 15.55, 0.55), B(7.405, 15.55, 0.55),
    B(7.405, 15.55, 0.43), B(7.405, 15.2, 0.43)], f => f.ahu.mCHW, f => f.ahu.TCHWSup, NOM.chw, 0.06, 14, true);
  flowPath([B(7.65, 15.2, 1.12), B(7.65, 15.85, 1.12), B(7.65, 15.85, 1.0), B(9.5, 15.85, 1.0), B(13.15, 15.85, 1.0), B(13.15, 14.7, 1.0), B(13.15, 14.7, 0.7)],
    f => f.ahu.mCHW, f => f.ahu.TCHWRet, NOM.chw, 0.06, 14, true);
}
const tmp = new THREE.Vector3();
function animateFlow(dt, f) {
  const show = document.getElementById('flow').checked;
  for (const p of paths) {
    const q = f ? Math.max(0, p.flow(f)) : 0;
    p.obj.visible = show && q > 0.004 && explode < 0.02 && isolateT < 0.05;
    if (!p.obj.visible) continue;
    const speed = 1.6 * Math.min(2, q / p.nominal) + 0.15;      // screen m/s, proportional to the mass flow
    const arr = p.geo.attributes.position.array;
    for (let k = 0; k < p.n; k++) {
      p.s[k] = (p.s[k] + speed * dt / p.len) % 1;
      p.curve.getPointAt(p.s[k], tmp).add(p.jitter[k]);
      arr[3 * k] = tmp.x; arr[3 * k + 1] = tmp.y; arr[3 * k + 2] = tmp.z;
    }
    p.geo.attributes.position.needsUpdate = true;
    (p.water ? waterColor : tempColor)(p.temp(f), p.m.color);
    p.m.opacity = 0.35 + 0.6 * clamp01(q / p.nominal);
  }
}

// ------------------------------------------------------------------ apply a frame to the scene
let last = null;
const people = { Eas: 5, Wes: 5, Int: 12 };
function rotBlades(prefix, n, axis, open, maxDeg = 80) {
  for (let k = 0; k < n; k++) {
    const o = nodes[`${prefix}_blade_${k}`]; if (!o) continue;
    o.rotation.set(0, 0, 0);
    o.rotation[axis] = (k % 2 ? -1 : 1) * clamp01(open) * maxDeg * Math.PI / 180;
  }
}
function applyFrame(f) {
  last = f;
  if (!ready) return;
  const mSup = Math.max(1e-6, f.ahu.mSup), on = f.on && f.ahu.mSup > 0.02;
  // AHU dampers: outdoor-air and relief open with their flows, return damper takes the rest
  const yOA = on ? clamp01(f.ahu.mOA / mSup / 0.5) : 0;
  rotBlades('ahu_damper_oa', 6, 'z', yOA);
  rotBlades('ahu_damper_ret', 4, 'z', on ? clamp01(1 - f.ahu.mOA / mSup) : 0);
  rotBlades('ahu_damper_rel', 5, 'x', on ? clamp01(f.ahu.mRel / mSup / 0.5) : 0);
  ZONES.forEach((z, i) => {
    const q = f.zones[i];
    const blade = nodes[`vav_${z}_damper_blade`];
    blade.rotation.set(0, 0, 0);
    blade.rotation[z === 'Int' ? 'x' : 'z'] = clamp01(q.yDam) * 80 * Math.PI / 180;
    const flap = nodes[`vav_${z}_backdraft_flap`];
    flap.rotation.set(0, 0, 0);
    flap.rotation[z === 'Int' ? 'x' : 'z'] = { Eas: 1, Wes: -1, Int: -1 }[z] * clamp01(q.mBox / NOM.box[i]) * 70 * Math.PI / 180;
    heaterMats[z].emissiveIntensity = 3.0 * clamp01(q.QReh / NOM.reh[i]);
    const occ = f.on ? Math.round(people[z] * clamp01(f.cfg.fGai[i] / 1.0)) : 0;
    for (let k = 0; k < people[z]; k++) { const o = nodes[`person_${z}_${k}`]; if (o) o.visible = k < occ; }
    tempColor(q.TZon, airMats[z].color);
    tempColor(q.TDis, plumeMats[z].color);
    plumeMats[z].opacity = 0.04 + 0.2 * clamp01(q.mBox / NOM.box[i]);
  });
  const stem = nodes['chw_control_valve_stem'];
  if (stem) stem.userData.animOff = new THREE.Vector3(0, 0.03 * clamp01(f.ahu.mCHW / NOM.chw), 0);
  updateScale(f);
  for (const p of parts) if (p.temp) { (p.name.startsWith('chw') ? waterColor : tempColor)(p.temp(f), p.thermal.color); p.thermal.emissive.copy(p.thermal.color).multiplyScalar(0.25); }

  document.getElementById('clock').textContent = `${f.clock}   ${f.on ? 'AHU on' : 'AHU off'}   outdoor ${f1(f.w.TOut)} °C, ${f1(100 * f.w.phiOut, 0)} % RH`;
  if (f.msg) document.getElementById('status').textContent = f.msg;
  const P_ = f.P;
  document.getElementById('power').innerHTML =
    `<span>Total</span><b>${f1(P_.tot / 1000, 2)} kW</b><span>Cooling plant</span><span>${f1(P_.coo / 1000, 2)} kW</span>` +
    `<span>Supply fan</span><span>${f1(P_.fan / 1000, 2)} kW</span><span>Reheat</span><span>${f1(P_.reh / 1000, 2)} kW</span>` +
    `<span>Supply air</span><span>${f1(f.ahu.TSup)} °C (set ${f1(f.ahu.TSupSet)} °C)</span>`;
  pushHistory(f);
  updateZoneLabels(f);
  updateCallouts(f);
  syncControls(f.cfg);
  if (hover && tipVisible) tip.textContent = hover.info(f);
}

// ------------------------------------------------------------------ zone labels (live values over each zone)
const zoneLabels = {};
for (const z of ZONES) {
  const d = document.createElement('div'); d.className = 'zlabel'; document.body.appendChild(d); zoneLabels[z] = d;
}
const ZLABEL_AT = { Wes: B(2, 6, 1.6), Int: B(9, 6, 1.6), Eas: B(16, 6, 1.6) };
function updateZoneLabels(f) {
  ZONES.forEach((z, i) => {
    const q = f.zones[i], c = f.cfg, sw = '#' + tempColor(q.TZon).getHexString();
    const mode = !f.on ? 'AHU off – floating' : q.yReh > 0.01 ? `heating ${f1(100 * q.yReh, 0)} %` : q.yCoo > 0.01 ? `cooling ${f1(100 * q.yCoo, 0)} %` : 'dead band';
    zoneLabels[z].innerHTML = `<b><i style="background:${sw}"></i>${ZNAME[z]} ${f1(q.TZon, 1)} °C</b>` +
      `<span>set ${f1(c.THeaSet[i], 1)}–${f1(c.TCooSet[i], 1)} °C · ${mode}</span>`;
  });
}
const _p = new THREE.Vector3();
function placeZoneLabels() {
  const show = document.getElementById('labels')?.checked && ready && last;
  for (const z of ZONES) {
    const d = zoneLabels[z];
    _p.copy(ZLABEL_AT[z]).add(byName[`zone_${z}`].group.position).project(camera);
    const vis = show && _p.z < 1 && Math.abs(_p.x) < 1.1 && Math.abs(_p.y) < 1.1 && byName[`zone_${z}`].group.visible;
    d.style.display = vis ? 'block' : 'none';
    if (vis) { d.style.left = `${(_p.x + 1) / 2 * innerWidth}px`; d.style.top = `${(1 - _p.y) / 2 * innerHeight}px`; }
  }
}

// ------------------------------------------------------------------ VAV call-outs: damper opening and reheat state, with leader lines
const svgNS = 'http://www.w3.org/2000/svg';
const leaderSvg = document.createElementNS(svgNS, 'svg');
leaderSvg.id = 'leaders'; document.body.appendChild(leaderSvg);
const callouts = [];
for (const z of ZONES) {
  for (const kind of ['damper', 'heater']) {
    const div = document.createElement('div'); div.className = `callout ${kind}`; document.body.appendChild(div);
    const line = document.createElementNS(svgNS, 'line'), dotEl = document.createElementNS(svgNS, 'circle');
    dotEl.setAttribute('r', 3.5); leaderSvg.append(line, dotEl);
    callouts.push({ z, kind, div, line, dot: dotEl, off: kind === 'damper' ? [-70, -95] : [70, -70] });
  }
}
function updateCallouts(f) {
  for (const c of callouts) {
    const i = zi(c.z), q = f.zones[i];
    if (c.kind === 'damper') {
      c.div.innerHTML = `<b>VAV ${ZNAME[c.z].split(' ')[0]} · damper ${f1(100 * q.yDam, 0)} % open</b>` +
        `<span>air ${f1(q.mBox, 2)} kg/s (${f1(100 * q.mBox / NOM.box[i], 0)} % of design)</span>`;
    } else {
      const on = q.QReh > 20;
      c.div.classList.toggle('on', on);
      c.div.innerHTML = on ? `<b>Reheat ON · ${f1(q.QReh / 1000, 2)} kW</b><span>${f1(100 * q.QReh / NOM.reh[i], 0)} % of ${f1(NOM.reh[i] / 1000, 1)} kW · discharge ${f1(q.TDis)} °C</span>`
        : `<b>Reheat OFF</b><span>discharge ${f1(q.TDis)} °C</span>`;
    }
  }
}
const _w = new THREE.Vector3(), _bb = new THREE.Box3();
function placeCallouts() {
  const show = document.getElementById('vavTags')?.checked && ready && last;
  const pos = {};
  for (const c of callouts) {
    const tgt = c.kind === 'damper' ? nodes[`vav_${c.z}_damper_blade`] : nodes[`vav_${c.z}_heater_element_1`];
    c.vis = show && tgt && byName[`vav_${c.z}`].group.visible;
    if (c.vis) {
      if (c.kind === 'damper') tgt.getWorldPosition(_w); else _bb.setFromObject(tgt).getCenter(_w);
      c.vis = _w.distanceTo(camera.position) < 30;
      _w.project(camera);
      c.vis = c.vis && _w.z < 1 && Math.abs(_w.x) < 1.05 && Math.abs(_w.y) < 1.05;
      c.x = (_w.x + 1) / 2 * innerWidth; c.y = (1 - _w.y) / 2 * innerHeight;
      (pos[c.z] ??= []).push(c);
    }
  }
  // the call-out whose target is further left on screen goes to the left, so the two leaders of a box never cross
  for (const z in pos) {
    const [a, b] = pos[z];
    if (!b) { a.side = -1; continue; }
    a.side = a.x <= b.x ? -1 : 1; b.side = -a.side;
  }
  for (const c of callouts) {
    c.div.style.display = c.vis ? 'block' : 'none';
    c.line.style.display = c.dot.style.display = c.vis ? '' : 'none';
    if (!c.vis) continue;
    const lx = c.x + c.side * 120, ly = c.y - 85;
    c.div.style.left = `${lx}px`; c.div.style.top = `${ly}px`;
    c.line.setAttribute('x1', lx); c.line.setAttribute('y1', ly); c.line.setAttribute('x2', c.x); c.line.setAttribute('y2', c.y);
    c.dot.setAttribute('cx', c.x); c.dot.setAttribute('cy', c.y);
  }
}

// ------------------------------------------------------------------ strip chart (last 24 h of simulated time)
const hist = [];
function pushHistory(f) {
  if (hist.length && f.t < hist.at(-1).t) hist.length = 0;
  if (!hist.length || f.t - hist.at(-1).t >= 300) hist.push({ t: f.t, P: f.P.tot / 1000, TS: f.ahu.TSup, phi: Math.max(...f.zones.map(q => q.phi)) });
  while (hist.length && f.t - hist[0].t > 86400) hist.shift();
  const c = document.getElementById('chart'), g = c.getContext('2d');
  g.clearRect(0, 0, c.width, c.height);
  if (hist.length < 2) return;
  const t0 = f.t - 86400, X = t => (t - t0) / 86400 * c.width;
  const line = (key, lo, hi, col) => {
    g.strokeStyle = col; g.lineWidth = 1.5; g.beginPath();
    hist.forEach((h, k) => { const y = c.height - 4 - (h[key] - lo) / (hi - lo) * (c.height - 8); k ? g.lineTo(X(h.t), y) : g.moveTo(X(h.t), y); });
    g.stroke();
  };
  line('P', 0, 15, '#e8e8e6'); line('TS', 10, 20, '#39a2fc'); line('phi', 0.4, 0.8, '#f3c63a');
  g.font = '10px system-ui';
  g.fillStyle = '#9a9893'; g.fillText('power 0–15 kW', 4, 10); g.fillStyle = '#39a2fc'; g.fillText('supply air 10–20 °C', 90, 10);
  g.fillStyle = '#f3c63a'; g.fillText('max RH 40–80 %', 200, 10);
}

// ------------------------------------------------------------------ backend connection and controls
let ws;
function connect() {
  ws = new (window.DemoSocket || WebSocket)(WS_URL);
  ws.onopen = () => (document.getElementById('status').textContent = 'connected');
  ws.onclose = () => { document.getElementById('status').textContent = 'backend not running – start start.bat'; setTimeout(connect, 2000); };
  ws.onmessage = e => applyFrame(JSON.parse(e.data));
}
connect();
const send = (key, value, index) => ws && ws.readyState === 1 && ws.send(JSON.stringify({ key, value, index }));

let editing = false;
document.querySelectorAll('input,select').forEach(el => { el.addEventListener('focus', () => (editing = true)); el.addEventListener('blur', () => (editing = false)); });
function seg(id, key) { document.querySelectorAll(`#${id} button`).forEach(b => (b.onclick = () => send(key, b.dataset.v))); }
seg('mode', 'mode'); seg('onMode', 'onMode');
const pauseBtn = document.getElementById('pause');
pauseBtn.onclick = () => send('paused', pauseBtn.textContent === 'Pause');
document.getElementById('speed').onchange = e => send('speed', +e.target.value);
const jumpBtn = document.getElementById('jump');
if (jumpBtn) jumpBtn.onclick = () => {
  const d = new Date(document.getElementById('day').value + 'T00:00:00Z');
  send('jumpDay', Math.round((d - Date.UTC(2023, 0, 1)) / 864e5));
};
const fix = document.getElementById('TSupFix');
fix.oninput = () => { document.getElementById('TSupFixV').textContent = `${(+fix.value).toFixed(1)} °C`; send('TSupFix', +fix.value); };
const foa = document.getElementById('fOA');
foa.oninput = () => { document.getElementById('fOAV').textContent = (+foa.value).toFixed(1); send('fOA', +foa.value); };
document.querySelectorAll('input.num').forEach(el => (el.onchange = () => send(el.dataset.k, +el.value, +el.dataset.i)));
function syncControls(c) {
  document.querySelectorAll('#mode button').forEach(b => b.classList.toggle('on', b.dataset.v === c.mode));
  document.querySelectorAll('#onMode button').forEach(b => b.classList.toggle('on', b.dataset.v === c.onMode));
  document.getElementById('fixRow').style.opacity = c.mode === 'fixed' ? 1 : 0.4;
  pauseBtn.textContent = c.paused ? 'Resume' : 'Pause';
  if (editing) return;
  document.querySelectorAll('input.num').forEach(el => (el.value = c[el.dataset.k][+el.dataset.i]));
}

// ------------------------------------------------------------------ view tools: explode, section, x-ray, isolate, ceiling, doors
let explode = 0, isolateT = 0, isolateGoal = 0, selected = null, selSet = new Set(), selName = '', doorT = 0, selLevel = 'equip';
const inSel = p => selSet.has(p);
document.getElementById('explode').oninput = e => { explode = +e.target.value; restack(); };
document.getElementById('explode').onchange = () => { if (selSet.size) document.getElementById('focus').click(); };
document.querySelectorAll('#selLevel button').forEach(b => (b.onclick = () => {
  selLevel = b.dataset.v;
  document.querySelectorAll('#selLevel button').forEach(x => x.classList.toggle('on', x === b));
  if (selected) select(selected);
}));
// recompute the exploded offsets for the current selection (or the whole system when nothing is selected)
function restack() {
  for (const p of parts) if (p.items) { clearItems(p.items); p.selOff = new THREE.Vector3(); }
  if (!selSet.size) return;
  const sc = boxCentre([...selSet].map(p => p.group));
  for (const p of selSet) {
    if (selSet.size > 1 && p.c0) { _d.subVectors(p.c0, sc); p.selOff = _d.clone().multiplyScalar(0.9 * explode).addScaledVector(_d.normalize(), 0.4 * explode); }
    spread(p.items, p.c0, explode, 0);
  }
}
const plane = new THREE.Plane(new THREE.Vector3(1, 0, 0), 0);
const secAxis = document.getElementById('secAxis'), secPos = document.getElementById('secPos');
function updateSection() {
  const a = secAxis.value;
  if (a === 'none') { renderer.clippingPlanes = []; return; }
  // x: west -> east, z: south -> north (three z is -north), y: floor -> plenum
  const range = { x: [-0.5, 18.5], z: [-0.5, 17.5], y: [0.05, 4.0] }[a], v = range[0] + (range[1] - range[0]) * +secPos.value;
  if (a === 'x') plane.set(new THREE.Vector3(-1, 0, 0), v);         // keep x < v
  if (a === 'z') plane.set(new THREE.Vector3(0, 0, 1), v);          // keep three z > -v, i.e. Blender y < v (south part)
  if (a === 'y') plane.set(new THREE.Vector3(0, -1, 0), v);         // keep below the cut height
  renderer.clippingPlanes = [plane];
}
secAxis.onchange = secPos.oninput = updateSection;
function applyXray() {
  const on = document.getElementById('xray').checked;
  for (const p of parts) for (const o of p.meshes) {
    const m = o.material;
    if (m.userData.op === undefined) { m.userData.op = m.opacity; m.userData.tr = m.transparent; m.userData.dw = m.depthWrite; }
    const fade = on && !(selSet.size && inSel(p)) && !o.userData.overlay;
    m.transparent = fade ? true : m.userData.tr;
    m.opacity = fade ? Math.min(m.userData.op, 0.12) : m.userData.op;
    m.depthWrite = fade ? false : m.userData.dw;
    m.needsUpdate = true;
  }
}
document.getElementById('xray').onchange = applyXray;
document.getElementById('ceiling').onchange = e => { byName.ceiling.group.visible = e.target.checked; };
document.getElementById('doors').onchange = () => {};
const isoBtn = document.getElementById('isolate');
isoBtn.onclick = () => { isolateGoal = 1; };
document.getElementById('showAll').onclick = () => { isolateGoal = 0; };
document.getElementById('home').onclick = () => { camera.position.copy(B(-5, -7, 16)); controls.target.copy(B(9, 9, 0.8)); };
document.getElementById('focus').onclick = () => {
  if (!selSet.size) return;
  const b = new THREE.Box3(); for (const p of selSet) b.expandByObject(p.group);
  const c = b.getCenter(new THREE.Vector3()), r = Math.max(1.2, b.getSize(new THREE.Vector3()).length());
  controls.target.copy(c);
  camera.position.copy(c).add(new THREE.Vector3(-0.6, 0.55, 0.9).normalize().multiplyScalar(r * (1.3 + 1.6 * explode)));
};

// picking: hover tooltip, click select
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2(), tip = document.getElementById('tip');
let hover = null, tipVisible = false;
renderer.domElement.addEventListener('pointermove', e => {
  if (!ready) return;
  mouse.set(e.clientX / innerWidth * 2 - 1, -e.clientY / innerHeight * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hits = ray.intersectObjects(pickables, false);
  const hit = hits.find(h => {
    let o = h.object; while (o) { if (!o.visible) return false; o = o.parent; }
    if (h.object.material.opacity < 0.15 && !inSel(h.object.userData.part)) return false;
    return !renderer.clippingPlanes.length || renderer.clippingPlanes[0].distanceToPoint(h.point) > 0;
  });
  hover = hit ? hit.object.userData.part : null;
  tipVisible = !!(hover && last);
  if (tipVisible) { tip.style.display = 'block'; tip.style.left = e.clientX + 14 + 'px'; tip.style.top = e.clientY + 14 + 'px'; tip.textContent = hover.info(last); }
  else tip.style.display = 'none';
});
let downAt = null;
renderer.domElement.addEventListener('pointerdown', e => (downAt = [e.clientX, e.clientY]));
renderer.domElement.addEventListener('click', e => {
  if (downAt && Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 4) return;   // a drag, not a click
  select(hover);
  applyXray();
});

function select(p) {
  selected = p; selSet = new Set(); selName = '';
  if (p) {
    const eq = selLevel === 'equip' ? EQUIP.find(([, re]) => re.test(p.name)) : null;
    if (eq) { for (const q of parts) if (eq[1].test(q.name) && q.meshes.length) selSet.add(q); selName = eq[0]; }
    else { selSet.add(p); selName = last ? p.info(last).split('\n')[0] : p.name; }
  }
  isoBtn.disabled = document.getElementById('focus').disabled = !p;
  document.getElementById('sel').textContent = p ? `Selected: ${selName}` : 'nothing selected – explode acts on the whole system';
  for (const q of parts) for (const m of q.matCache.values()) if (m.emissive && !Object.values(heaterMats).includes(m)) {
    m.userData.e0 ??= m.emissive.getHex();
    m.emissive.setHex(inSel(q) ? 0x1d3550 : m.userData.e0);
  }
  if (!p) isolateGoal = 0;
  restack();
  applyXray();
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') select(null); });

// ------------------------------------------------------------------ render loop
window.__viz = { camera, controls, B, nodes, parts, select, byName };
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(0.05, clock.getDelta());
  if (ready) {
    isolateT += (isolateGoal - isolateT) * Math.min(1, dt * 3);
    doorT += ((document.getElementById('doors').checked ? 1 : 0) - doorT) * Math.min(1, dt * 3);
    for (const p of parts) {
      const away = selSet.size && !inSel(p) ? isolateT : 0;
      // no selection: the whole system explodes part by part; with a selection only the selected unit comes apart,
      // down to its sub-assemblies, while isolate sends everything else outwards before hiding it
      p.group.position.copy(p.dir).multiplyScalar((selSet.size ? 0 : explode) + away * 3.0);
      if (p.selOff && inSel(p)) p.group.position.add(p.selOff);
      if (p.items) placeItems(p.items);
      p.group.visible = away < (p.dir.lengthSq() < 1e-6 ? 0.3 : 0.95) && (p.name !== 'ceiling' || document.getElementById('ceiling').checked);
    }
    for (const s of ['mix', 'filter', 'fan', 'coil', 'dis']) { const d = nodes[`ahu_${s}_door`]; if (d) d.rotation.y = -doorT * 1.75; }
    if (last) {
      const imp = nodes['ahu_fan_impeller']; if (imp) imp.rotation.x -= dt * 30 * clamp01(last.ahu.mSup / NOM.sup);
      const cf = clamp01(last.ahu.QCoi / NOM.qcoi);
      for (const k of [0, 1]) { const o = nodes[`chiller_fan_${k}`]; if (o) o.rotation.y += dt * (cf > 0.02 ? 6 + 18 * cf : 0); }
      const pc = nodes['chw_pump_shaft_coupling']; if (pc) pc.rotation.y += dt * 40 * clamp01(last.ahu.mCHW / NOM.chw);
    }
  }
  animateFlow(dt, last);
  controls.update();
  placeZoneLabels();
  placeCallouts();
  renderer.render(scene, camera);
});
