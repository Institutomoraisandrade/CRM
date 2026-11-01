'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { createTimeline, stagger, utils } from 'animejs';
import { montaCena } from './cena';
import { Topo } from '../Topo';

const PALAVRAS = ['Seu', 'caminhão', 'de', 'volta'], DESTAQUE = ['à', 'estrada.'];

export function Hero() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const cena = useRef<ReturnType<typeof montaCena>>(null);
  const [farois, setFarois] = useState(false);
  const [pausado, setPausado] = useState(false);
  const anos = useRef<HTMLElement>(null);

  useEffect(() => {
    const reduz = matchMedia('(prefers-reduced-motion: reduce)').matches;
    setPausado(reduz);
    cena.current = montaCena(canvas.current!, reduz);
    const est = cena.current?.estado;
    if (!reduz) {
      const ent = document.querySelectorAll('.js-in'), pal = document.querySelectorAll('.js-w');
      utils.set(pal, { y: '110%' }); utils.set(ent, { opacity: 0, y: 24 });
      const cont = { n: 0 };
      const tl = createTimeline({ defaults: { ease: 'outQuint' } });
      if (est) tl.add(est, { truckZ: 0, duration: 2600, ease: 'outExpo' }, 0).add(est, { farol: [0.35, 1, 0.35], duration: 900, ease: 'inOutQuad' }, 1700);
      tl.add(ent[0], { opacity: 1, y: 0, duration: 700 }, 300)
        .add(pal, { y: '0%', duration: 900, delay: stagger(70) }, 450)
        .add([...ent].slice(1), { opacity: 1, y: 0, duration: 800, delay: stagger(110) }, 1000)
        .add(cont, { n: 24, duration: 1400, ease: 'outQuad', modifier: utils.round(0), onUpdate: () => { if (anos.current) anos.current.textContent = String(cont.n); } }, 1500);
    } else if (anos.current) anos.current.textContent = '24';
    return () => cena.current?.destroi();
  }, []);

  const palavra = (p: string, em = false) => (
    <span key={p}><span className="inline-block overflow-hidden pb-1 align-bottom"><span className={`js-w inline-block ${em ? 'text-amarelo not-italic' : ''}`}>{p}</span></span>{' '}</span>
  );

  return (
    <section id="topo" aria-label="Apresentação" className="relative h-svh max-h-[960px] min-h-[640px] overflow-hidden bg-marinho text-white">
      <canvas ref={canvas} aria-hidden className="absolute inset-0 h-full w-full" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-marinho/90 via-marinho/40 to-transparent" />
      <Topo escuro />
      <div className="relative z-10 flex h-full max-w-2xl flex-col justify-center px-5 pt-20 md:px-16">
        <span className="js-in mb-5 flex items-center gap-3 font-display text-sm font-bold tracking-[.22em] text-suave">
          <span aria-hidden className="flex gap-1">{[40, 20, 10].map((w) => <i key={w} style={{ width: w }} className="h-1 bg-amarelo" />)}</span>
          PEÇAS E SERVIÇOS PARA CAMINHÕES
        </span>
        <h1 className="font-display text-6xl font-extrabold uppercase leading-[.9] md:text-8xl">
          {PALAVRAS.map((p) => palavra(p))}<br />{DESTAQUE.map((p) => palavra(p, true))}
        </h1>
        <p className="js-in mt-6 max-w-lg text-lg text-suave">Peças e serviços em um só lugar, para caminhoneiros autônomos e frotas. Compre online ou receba seu orçamento pelo WhatsApp.</p>
        <div className="js-in mt-8 flex flex-wrap gap-3">
          <Link href="/orcamento" className="btn btn-sinal btn-lg">Pedir orçamento</Link>
          <Link href="/catalogo" className="btn btn-contorno btn-lg">Ver catálogo</Link>
        </div>
        <div className="js-in mt-10 flex gap-10">
          <div><b ref={anos} className="font-display text-5xl font-extrabold text-amarelo">0</b><span className="block text-sm text-suave">anos de atuação <small>[dado a validar]</small></span></div>
          <div><b className="font-display text-5xl font-extrabold text-amarelo">2</b><span className="block text-sm text-suave">frentes: peças<br />e serviços</span></div>
        </div>
      </div>
      <div className="absolute bottom-6 right-5 z-10 flex gap-2 md:right-16">
        <button type="button" aria-pressed={farois} className="btn btn-contorno h-10 min-h-0 px-4 text-sm" onClick={() => { setFarois(!farois); cena.current?.farois(!farois); }}>Faróis</button>
        <button type="button" aria-pressed={pausado} className="btn btn-contorno h-10 min-h-0 px-4 text-sm" onClick={() => { setPausado(!pausado); cena.current?.pausar(!pausado); }}>{pausado ? 'Andar' : 'Pausar'}</button>
      </div>
    </section>
  );
}
