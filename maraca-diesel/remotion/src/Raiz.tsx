import { Composition } from 'remotion';
import { Reveal } from './Reveal';
import { Oferta, type OfertaProps } from './Oferta';

// 9:16 para Reels/Stories/TikTok/Shorts. 30 fps.
export const Raiz = () => (
  <>
    <Composition id="Reveal" component={Reveal} durationInFrames={300} fps={30} width={1080} height={1920} />
    <Composition id="Oferta" component={Oferta} durationInFrames={240} fps={30} width={1080} height={1920}
      defaultProps={{ produto: 'Filtro de óleo', codigo: 'FI-001', preco: 'R$ 89,90', chamada: 'Compre no site ou peça orçamento' } satisfies OfertaProps} />
  </>
);
