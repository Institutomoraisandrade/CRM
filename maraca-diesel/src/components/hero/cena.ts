/* Cena 3D do hero (porta do protótipo "Maracá Diesel Hero 3D").
   Caminhão genérico low-poly (sem marca de terceiros), estrada infinita e partículas. */
import * as T from 'three';
import { animate, createAnimatable, utils } from 'animejs';

export type Estado = { intro: number; truckZ: number; vel: number; camX: number; camY: number; farol: number; scroll: number; pausado: boolean; mobile?: boolean };

export function montaCena(canvas: HTMLCanvasElement, reduz: boolean) {
  let renderer: T.WebGLRenderer;
  try { renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: false }); } catch { return null; }
  const estado: Estado = { intro: reduz ? 1 : 0, truckZ: reduz ? 0 : -46, vel: reduz ? 0 : 1, camX: 0, camY: 0, farol: 0.35, scroll: 0, pausado: reduz };
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  renderer.outputColorSpace = T.SRGBColorSpace;
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  const cena = new T.Scene();
  const fundo = new T.Color('#0a2350');
  cena.background = fundo;
  cena.fog = new T.Fog(fundo, 26, 80);
  const cam = new T.PerspectiveCamera(32, 1, 0.1, 200);
  cena.add(new T.HemisphereLight('#d6e2ff', '#16284a', 1.7));
  const sol = new T.DirectionalLight('#ffffff', 2.4);
  sol.position.set(-10, 16, 10);
  sol.castShadow = true;
  sol.shadow.mapSize.set(2048, 2048);
  Object.assign(sol.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 60 });
  sol.shadow.bias = -0.0004;
  cena.add(sol);
  const contra = new T.DirectionalLight('#7fa3ff', 1.2);
  contra.position.set(12, 6, -14);
  cena.add(contra);
/* chão e estrada */
const chao = new T.Mesh(new T.PlaneGeometry(200, 200), new T.MeshStandardMaterial({ color: '#0c2754', roughness: 1 }));
chao.rotation.x = -Math.PI / 2; chao.receiveShadow = true; cena.add(chao);
const estrada = new T.Mesh(new T.PlaneGeometry(9, 200), new T.MeshStandardMaterial({ color: '#16243b', roughness: .92 }));
estrada.rotation.x = -Math.PI / 2; estrada.position.y = 0.005; estrada.receiveShadow = true; cena.add(estrada);
const matBranco = new T.MeshStandardMaterial({ color: '#dfe6f2', roughness: .6 });
[-4.2, 4.2].forEach(x => { const l = new T.Mesh(new T.PlaneGeometry(0.16, 200), matBranco); l.rotation.x = -Math.PI / 2; l.position.set(x, 0.01, 0); cena.add(l); });
const matFaixa = new T.MeshStandardMaterial({ color: '#ffc20e', emissive: '#ffc20e', emissiveIntensity: .25, roughness: .5 });
const faixas: T.Mesh[] = [];
const PASSO = 6;
for (let i = 0; i < 30; i++) {
  const f = new T.Mesh(new T.PlaneGeometry(0.22, 3), matFaixa);
  f.rotation.x = -Math.PI / 2; f.position.set(0, 0.012, -90 + i * PASSO); cena.add(f); faixas.push(f);
}
/* postes de acostamento para dar velocidade */
const postes: T.Group[] = [];
const matPoste = new T.MeshStandardMaterial({ color: '#cfd8e6', roughness: .5 });
const matRefl = new T.MeshStandardMaterial({ color: '#ffc20e', emissive: '#ffc20e', emissiveIntensity: .6 });
for (let i = 0; i < 16; i++) {
  [-5.6, 5.6].forEach(x => {
    const g = new T.Group();
    const p = new T.Mesh(new T.BoxGeometry(0.12, 1, 0.12), matPoste); p.position.y = .5; g.add(p);
    const r = new T.Mesh(new T.BoxGeometry(0.13, 0.16, 0.13), matRefl); r.position.y = .86; g.add(r);
    g.position.set(x, 0, -90 + i * 12); cena.add(g); postes.push(g);
  });
}

/* ---------- caminhão genérico (cavalo + semirreboque) ---------- */
const caminhao = new T.Group();
const M = (c: string, o: Partial<T.MeshStandardMaterialParameters> = {}) => new T.MeshStandardMaterial(Object.assign({ color: c, roughness: .45, metalness: .15 }, o));
const azul = M('#1746a2', { roughness: .32, metalness: .35 });
const marinho = M('#0a2350', { roughness: .4 });
const amarelo = M('#ffc20e', { roughness: .35 });
const grafite = M('#1c2433', { roughness: .7 });
const metal = M('#9aa6b8', { roughness: .25, metalness: .85 });
const vidro = M('#0b1a33', { roughness: .08, metalness: .6, envMapIntensity: 1 });
const pneu = M('#0e1117', { roughness: .95 });
const branco = M('#f4f6fa', { roughness: .5 });
const farolMat = new T.MeshStandardMaterial({ color: '#fff7d6', emissive: '#fff2c0', emissiveIntensity: 1 });
const lanternaMat = new T.MeshStandardMaterial({ color: '#ff9a3c', emissive: '#ff8a1c', emissiveIntensity: .8 });

function caixa(w: number, h: number, d: number, mat: T.Material, x: number, y: number, z: number, sombra = true) {
  const m = new T.Mesh(new T.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = sombra; m.receiveShadow = true; caminhao.add(m); return m;
}
const rodas: T.Group[] = [];
function roda(x: number, z: number, dupla: boolean) {
  const g = new T.Group();
  const geo = new T.CylinderGeometry(0.52, 0.52, dupla ? 0.62 : 0.36, 28);
  const p = new T.Mesh(geo, pneu); p.rotation.z = Math.PI / 2; p.castShadow = true; g.add(p);
  const aro = new T.Mesh(new T.CylinderGeometry(0.3, 0.3, (dupla ? 0.62 : 0.36) + 0.02, 18), metal); aro.rotation.z = Math.PI / 2; g.add(aro);
  const cubo = new T.Mesh(new T.BoxGeometry((dupla ? 0.64 : 0.38), 0.1, 0.42), grafite); g.add(cubo);
  g.position.set(x, 0.52, z); caminhao.add(g); rodas.push(g);
}

/* cabine cab-over estilo europeu (referência visual: frente de Volvo FH — grade alta, faróis em "V",
   para-sol e teto alto). Sem logotipo ou elementos de marca registrada. */
const zFrente = 4.6;
caixa(2.5, 2.5, 2.25, azul, 0, 2.38, zFrente - 1.12);             /* corpo */
caixa(2.46, 0.95, 2.05, azul, 0, 4.05, zFrente - 1.22);           /* teto alto (Globetrotter) */
caixa(2.5, 0.12, 0.5, marinho, 0, 3.52, zFrente + 0.12);          /* para-sol */
caixa(2.34, 1.0, 0.06, vidro, 0, 2.98, zFrente + 0.005, false);   /* para-brisa */
caixa(0.06, 0.85, 1.0, vidro, -1.255, 2.98, zFrente - 0.6, false);
caixa(0.06, 0.85, 1.0, vidro, 1.255, 2.98, zFrente - 0.6, false);
caixa(2.52, 0.12, 2.27, amarelo, 0, 2.36, zFrente - 1.12);         /* faixa amarela */
/* grade alta trapezoidal: lâminas horizontais que alargam para baixo */
caixa(1.9, 1.15, 0.06, grafite, 0, 1.78, zFrente + 0.02);
for (let i = 0; i < 7; i++) caixa(1.5 + i * 0.06, 0.06, 0.05, metal, 0, 1.3 + i * 0.15, zFrente + 0.07, false);
caixa(1.98, 0.08, 0.08, metal, 0, 2.38, zFrente + 0.06, false);    /* moldura cromada superior */
caixa(2.58, 0.48, 0.4, grafite, 0, 0.98, zFrente);                  /* para-choque */
caixa(2.0, 0.08, 0.06, metal, 0, 0.82, zFrente + 0.21, false);
/* faróis em "V": bloco inclinado + DRL em linha */
const farolE = caixa(0.6, 0.2, 0.08, farolMat, -1.0, 1.28, zFrente + 0.15, false); farolE.rotation.z = -0.32;
const farolD = caixa(0.6, 0.2, 0.08, farolMat, 1.0, 1.28, zFrente + 0.15, false); farolD.rotation.z = 0.32;
const drlE = caixa(0.42, 0.04, 0.06, farolMat, -1.02, 1.5, zFrente + 0.15, false); drlE.rotation.z = 0.55;
const drlD = caixa(0.42, 0.04, 0.06, farolMat, 1.02, 1.5, zFrente + 0.15, false); drlD.rotation.z = -0.55;
caixa(2.0, 0.1, 0.1, farolMat, 0, 4.55, zFrente - 0.3, false);    /* barra de luz no teto */
[-1.42, 1.42].forEach(x => {                                       /* retrovisores */
  caixa(0.06, 0.06, 0.5, grafite, x * 0.94, 3.1, zFrente - 0.25, false);
  caixa(0.12, 0.7, 0.22, marinho, x, 3.0, zFrente - 0.02);
});
caixa(0.5, 0.06, 0.6, grafite, -1.1, 1.0, zFrente - 1.6);          /* degrau */
/* chassi e tanque */
caixa(1.0, 0.3, 9.4, grafite, 0, 1.05, -0.4);
const tanque = new T.Mesh(new T.CylinderGeometry(0.36, 0.36, 1.5, 24), metal);
tanque.rotation.x = Math.PI / 2; tanque.position.set(-1.0, 1.0, 1.2); tanque.castShadow = true; caminhao.add(tanque);
caixa(0.3, 0.3, 0.6, grafite, 1.0, 1.05, 1.4);
/* escape vertical */
const escape = new T.Mesh(new T.CylinderGeometry(0.08, 0.08, 1.8, 12), metal);
escape.position.set(1.15, 3.2, zFrente - 2.35); caminhao.add(escape);
/* quinta roda */
caixa(1.4, 0.12, 1.2, grafite, 0, 1.28, -2.2);
/* rodas do cavalo */
roda(-1.05, zFrente - 1.0, false); roda(1.05, zFrente - 1.0, false);
roda(-1.0, -1.6, true); roda(1.0, -1.6, true);
roda(-1.0, -2.9, true); roda(1.0, -2.9, true);
/* para-lamas traseiros */
caixa(2.6, 0.08, 2.3, grafite, 0, 1.15, -2.25);

/* semirreboque */
const zR = -9.4;
caixa(2.55, 2.9, 12.2, branco, 0, 3.0, zR);
caixa(2.57, 0.34, 12.22, azul, 0, 1.72, zR);
caixa(2.58, 0.16, 12.23, amarelo, 0, 2.0, zR);
caixa(2.58, 0.08, 12.23, marinho, 0, 4.42, zR);
caixa(2.6, 0.2, 0.1, grafite, 0, 1.4, zR - 6.12);
[-1.0, 1.0].forEach((x) => void caixa(0.3, 0.14, 0.06, lanternaMat, x, 1.6, zR - 6.14, false));
caixa(1.1, 0.3, 11.5, grafite, 0, 1.38, zR + 0.2);
[-12.6, -13.9, -15.2].forEach((z) => { roda(-1.0, z, true); roda(1.0, z, true); });
caixa(2.6, 0.08, 4.2, grafite, 0, 1.15, -13.9);

/* fachos de luz dos faróis */
const facho = (x: number) => {
  const s = new T.SpotLight('#fff3cc', 0, 30, Math.PI / 7, 0.55, 1.2);
  s.position.set(x, 1.25, zFrente + 0.2);
  s.target.position.set(x * 1.6, 0, zFrente + 14);
  caminhao.add(s); caminhao.add(s.target); return s;
};
const fachos = [facho(-0.98), facho(0.98)];

caminhao.rotation.y = 0;
cena.add(caminhao);

/* poeira / partículas de velocidade */
const NP = 220;
const pg = new T.BufferGeometry();
const pos = new Float32Array(NP * 3);
for (let i = 0; i < NP; i++) { pos[i * 3] = (utils.random(-14, 14, 2) as number); pos[i * 3 + 1] = (utils.random(0.2, 6, 2) as number); pos[i * 3 + 2] = (utils.random(-80, 20, 2) as number); }
pg.setAttribute('position', new T.BufferAttribute(pos, 3));
const pontos = new T.Points(pg, new T.PointsMaterial({ color: '#9fb6e6', size: 0.06, transparent: true, opacity: .55 }));
cena.add(pontos);

  const alvo = new T.Vector3();
  function enquadra() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    cam.aspect = w / h;
    const mobile = w < 900;
    cam.fov = mobile ? 40 : 30;
    cam.updateProjectionMatrix();
    estado.mobile = mobile;
  }
  enquadra();
  window.addEventListener('resize', enquadra);

  const mira = createAnimatable(estado, { camX: 900, camY: 900, ease: 'outQuint' });
  const onMove = (e: PointerEvent) => {
    if (reduz) return;
    (mira.camX as (v: number) => void)((e.clientX / window.innerWidth - 0.5) * 2);
    (mira.camY as (v: number) => void)((e.clientY / window.innerHeight - 0.5) * 2);
  };
  window.addEventListener('pointermove', onMove);
  const onScrollWin = () => { estado.scroll = Math.min(1, window.scrollY / Math.max(1, canvas.clientHeight)); };
  window.addEventListener('scroll', onScrollWin, { passive: true });

  let odometro = 0, ultimo = performance.now(), raf = 0, vivo = true;
  function quadro(agora: number) {
    if (!vivo) return;
    const dt = Math.min((agora - ultimo) / 1000, 0.05); ultimo = agora;
    const v = estado.pausado ? 0 : estado.vel;
    const desloc = v * 16 * dt;
    odometro += desloc;
    faixas.forEach(f => { f.position.z += desloc; if (f.position.z > 30) f.position.z -= 30 * PASSO; });
    postes.forEach(p => { p.position.z += desloc; if (p.position.z > 30) p.position.z -= 16 * 12; });
    const a = pg.attributes.position as T.BufferAttribute;
    for (let i = 0; i < NP; i++) { let z = a.getZ(i) + desloc * 1.6; if (z > 22) z -= 100; a.setZ(i, z); }
    a.needsUpdate = true;
    rodas.forEach(r => { r.rotation.x += desloc / 0.52; });
    const bob = v > 0 ? Math.sin(odometro * 1.9) * 0.025 + Math.sin(odometro * 4.3) * 0.01 : 0;
    caminhao.position.set(0, bob, estado.truckZ + estado.scroll * 10);
    farolMat.emissiveIntensity = 0.6 + estado.farol * 2.4;
    fachos.forEach(s => s.intensity = estado.farol * 60);
    const m = estado.mobile;
    const ox = (m ? 0.2 : -8.4) * estado.intro;
    const raio = m ? 21 : 25;
    const ang = ((m ? 0.72 : 0.86) * estado.intro) + estado.camX * 0.1;
    cam.position.set(Math.sin(ang) * raio + ox * 0.2, (m ? 5.2 : 4.6) + estado.camY * -0.5 - estado.scroll * 1.6, Math.cos(ang) * raio + (m ? 0 : 1));
    alvo.set(ox, m ? 2.2 : 2.4, (m ? -3.5 : -2.5) + estado.scroll * 6);
    cam.lookAt(alvo);
    renderer.render(cena, cam);
    raf = requestAnimationFrame(quadro);
  }
  raf = requestAnimationFrame(quadro);

  return {
    estado,
    farois(on: boolean) { animate(estado, { farol: on ? 1 : 0.35, duration: reduz ? 0 : 500, ease: 'outQuad' }); },
    pausar(p: boolean) { estado.pausado = p; },
    destroi() {
      vivo = false; cancelAnimationFrame(raf);
      window.removeEventListener('resize', enquadra);
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('scroll', onScrollWin);
      renderer.dispose();
    },
  };
}
