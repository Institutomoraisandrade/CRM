import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, display, sans } from './marca';

export type OfertaProps = { produto: string; codigo: string; preco: string; chamada: string };

/* Template de criativo de remarketing (catálogo dinâmico): faixas amarelas entram como marcação de estrada,
   nome da peça sobe palavra por palavra, preço "carimba", CTA pulsa. Gera 1 vídeo por produto via --props. */
export const Oferta = ({ produto, codigo, preco, chamada }: OfertaProps) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const sp = (d: number, damping = 200) => spring({ frame: f - d, fps, config: { damping } });
  const faixa = (i: number) => interpolate(f, [i * 4, i * 4 + 20], [-1200, 0], { extrapolateRight: 'clamp', extrapolateLeft: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.marinho, padding: 90, fontFamily: sans, color: C.branco }}>
      {[0, 1, 2].map((i) => <div key={i} style={{ height: 22, width: [360, 180, 90][i], background: C.amarelo, marginBottom: 16, transform: `translateX(${faixa(i)}px)` }} />)}
      <div style={{ marginTop: 80, fontSize: 40, letterSpacing: 10, color: C.suave, opacity: sp(20) }}>CÓD. {codigo}</div>
      <div style={{ fontFamily: display, fontWeight: 800, fontSize: 170, lineHeight: 0.9, textTransform: 'uppercase', marginTop: 30 }}>
        {produto.split(' ').map((p, i) => (
          <span key={i} style={{ display: 'inline-block', overflow: 'hidden', marginRight: 30 }}>
            <span style={{ display: 'inline-block', transform: `translateY(${(1 - sp(30 + i * 5)) * 110}%)` }}>{p}</span>
          </span>))}
      </div>
      <div style={{ marginTop: 80, fontFamily: display, fontWeight: 800, fontSize: 220, color: C.amarelo, transform: `scale(${sp(80, 10)}) rotate(${(1 - sp(80, 10)) * -8}deg)`, transformOrigin: 'left center' }}>{preco}</div>
      <div style={{ position: 'absolute', bottom: 160, left: 90, right: 90, background: C.amarelo, color: C.tinta, fontWeight: 700, fontSize: 54, padding: 40, borderRadius: 10, textAlign: 'center',
        transform: `scale(${sp(130, 12) * (1 + Math.sin(f / 6) * 0.015)})` }}>{chamada}</div>
    </AbsoluteFill>
  );
};
