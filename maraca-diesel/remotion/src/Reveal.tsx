import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import { Caminhao } from './Caminhao';
import { C, display, sans } from './marca';

/* Estrutura inspirada nos lançamentos de caminhão (Volvo/Scania): escuro → farol acende → câmera orbita em
   close de detalhes → revelação do veículo inteiro → claim → CTA. 10 s, 9:16. */
export const Reveal = () => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const farol = interpolate(f, [15, 30, 45], [0, 1, 0.6], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const luz = interpolate(f, [0, 60], [0.05, 1.6], { extrapolateRight: 'clamp' });
  const ang = interpolate(f, [0, 210], [0.15, 1.1], { easing: Easing.inOut(Easing.cubic), extrapolateRight: 'clamp' });
  const raio = interpolate(f, [0, 210], [9, 26], { easing: Easing.inOut(Easing.cubic), extrapolateRight: 'clamp' });
  const z = interpolate(f, [150, 300], [0, 14], { extrapolateLeft: 'clamp' });
  const titulo = spring({ frame: f - 200, fps, config: { damping: 200 } });
  const cta = spring({ frame: f - 240, fps, config: { damping: 14 } });
  return (
    <AbsoluteFill style={{ background: C.marinho }}>
      <ThreeCanvas width={width} height={height} shadows camera={{ fov: 38, position: [Math.sin(ang) * raio, 2.2 + raio * 0.12, Math.cos(ang) * raio + z] }}
        onCreated={({ camera }) => camera.lookAt(0, 2, z - 2)}>
        <color attach="background" args={[C.marinho]} /><fog attach="fog" args={[C.marinho, 20, 70]} />
        <hemisphereLight args={['#d6e2ff', '#16284a', luz]} />
        <directionalLight position={[-10, 16, 10]} intensity={luz * 1.5} castShadow />
        <group position={[0, 0, z]}><Caminhao giro={f * 0.4} farol={farol} /></group>
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow><planeGeometry args={[9, 300]} /><meshStandardMaterial color="#16243b" /></mesh>
      </ThreeCanvas>
      <Sequence from={200}>
        <AbsoluteFill style={{ justifyContent: 'flex-end', padding: 90, paddingBottom: 380 }}>
          <div style={{ fontFamily: display, fontWeight: 800, color: C.branco, fontSize: 150, lineHeight: 0.9, textTransform: 'uppercase', opacity: titulo, transform: `translateY(${(1 - titulo) * 80}px)` }}>
            Seu caminhão<br />de volta <span style={{ color: C.amarelo }}>à estrada.</span>
          </div>
        </AbsoluteFill>
      </Sequence>
      <Sequence from={240}>
        <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'flex-start', padding: 90, paddingBottom: 200 }}>
          <div style={{ transform: `scale(${cta})`, background: C.amarelo, color: C.tinta, fontFamily: sans, fontWeight: 700, fontSize: 52, padding: '28px 48px', borderRadius: 8 }}>maracadiesel.com.br · Peça orçamento</div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
