// Caminhão low-poly (mesma geometria do hero do site), em R3F para o Remotion.
const B = ({ s, p, c, e = 0 }: { s: [number, number, number]; p: [number, number, number]; c: string; e?: number }) => (
  <mesh position={p} castShadow receiveShadow><boxGeometry args={s} /><meshStandardMaterial color={c} emissive={e ? c : '#000'} emissiveIntensity={e} roughness={0.4} metalness={0.2} /></mesh>
);
const Roda = ({ x, z, giro, dupla }: { x: number; z: number; giro: number; dupla?: boolean }) => (
  <group position={[x, 0.52, z]} rotation={[giro, 0, 0]}>
    <mesh rotation={[0, 0, Math.PI / 2]} castShadow><cylinderGeometry args={[0.52, 0.52, dupla ? 0.62 : 0.36, 28]} /><meshStandardMaterial color="#0e1117" roughness={0.95} /></mesh>
    <mesh rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.3, 0.3, (dupla ? 0.62 : 0.36) + 0.02, 18]} /><meshStandardMaterial color="#9aa6b8" metalness={0.85} roughness={0.25} /></mesh>
  </group>
);
export const Caminhao = ({ giro, farol }: { giro: number; farol: number }) => {
  const zF = 4.6;
  return (
    <group>
      <B s={[2.5, 2.35, 2.25]} p={[0, 2.3, zF - 1.12]} c="#1746a2" />
      <B s={[2.46, 0.7, 2]} p={[0, 3.82, zF - 1.25]} c="#1746a2" />
      <B s={[2.3, 1.05, 0.06]} p={[0, 2.95, zF]} c="#0b1a33" />
      <B s={[2.52, 0.14, 2.27]} p={[0, 2.28, zF - 1.12]} c="#ffc20e" />
      <B s={[1.7, 0.78, 0.08]} p={[0, 1.72, zF + 0.02]} c="#1c2433" />
      <B s={[2.56, 0.42, 0.34]} p={[0, 1.0, zF - 0.02]} c="#1c2433" />
      <B s={[0.42, 0.2, 0.06]} p={[-0.98, 1.22, zF + 0.17]} c="#fff2c0" e={0.6 + farol * 2.4} />
      <B s={[0.42, 0.2, 0.06]} p={[0.98, 1.22, zF + 0.17]} c="#fff2c0" e={0.6 + farol * 2.4} />
      <B s={[2.0, 0.1, 0.1]} p={[0, 4.17, zF - 0.62]} c="#fff2c0" e={0.6 + farol * 2.4} />
      <B s={[1.0, 0.3, 9.4]} p={[0, 1.05, -0.4]} c="#1c2433" />
      <B s={[2.55, 2.9, 12.2]} p={[0, 3.0, -9.4]} c="#f4f6fa" />
      <B s={[2.57, 0.34, 12.22]} p={[0, 1.72, -9.4]} c="#1746a2" />
      <B s={[2.58, 0.16, 12.23]} p={[0, 2.0, -9.4]} c="#ffc20e" />
      {[[zF - 1, false], [-1.6, true], [-2.9, true], [-12.6, true], [-13.9, true], [-15.2, true]].map(([z, d]) =>
        [-1.03, 1.03].map((x) => <Roda key={`${x}${z}`} x={x} z={z as number} dupla={d as boolean} giro={giro} />))}
    </group>
  );
};
