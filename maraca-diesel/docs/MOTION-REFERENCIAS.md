# Referências de motion — fabricantes de caminhão

O que observamos nos lançamentos e redes de Volvo Trucks e Scania, e como foi aplicado (sem copiar marcas, modelos ou peças deles; o caminhão do site é genérico).

| Padrão nas referências | Onde vimos | Aplicação na Maracá Diesel |
|---|---|---|
| **Revelação no escuro**: veículo surge da sombra, faróis acendem primeiro | Lançamentos da nova geração Scania (transmissão ao vivo, teasers com só o farol) | Hero: caminhão entra do fundo da estrada, faróis piscam aos 1,7 s; Remotion `Reveal` começa com cena escura e farol |
| **Prova de engenharia como espetáculo** (stunt real, câmera estável, um plano longo) | Volvo "The Epic Split" (2013) e "The Tower" (2020), Forsman & Bodenfors | Câmera com movimento lento e contínuo (órbita) em vez de cortes rápidos |
| **CGI + simulação** para mostrar o que a câmera não pega | Volvo FH LNG "The Surge" (2017) | Partículas de poeira/velocidade, estrada infinita, câmera que acompanha a rolagem |
| **Tipografia condensada grande, caixa-alta, entra por máscara** | Posts de Instagram das duas marcas | Barlow Condensed 800, palavras sobem de dentro de uma máscara (stagger 70 ms) |
| **Uma cor de sinal só** (amarelo/alerta) sobre fundo frio | Identidade visual de sinalização rodoviária | Amarelo `#ffc20e` reservado para CTA, faixas e números |
| **Formato vertical curto, CTA nos 2 s finais** | Reels/Shorts das marcas | Remotion 1080×1920, 8–10 s, CTA com spring |

## Regras de motion do projeto
- Easing padrão `outQuint` / `outExpo`; nada linear exceto rolagem.
- Duração 600–900 ms para textos; stagger 70–110 ms.
- Tudo desligável: `prefers-reduced-motion` e botão Pausar.
- 3D leve: geometrias primitivas, sem texturas pesadas, `pixelRatio ≤ 2`.

## Fontes
- [The Epic Split — Wikipedia](https://en.wikipedia.org/wiki/The_Epic_Split)
- [Fast Company — Como a Volvo Trucks fez o Epic Split](https://www.fastcompany.com/3031654/how-volvo-trucks-pulled-off-an-epic-split-and-a-game-changing-campaign)
- [LBBOnline — Volvo "The Tower"](https://lbbonline.com/news/volvo-built-a-tower-from-four-of-its-new-trucks-in-another-epic-stunt)
- [Ads of the World — Volvo Trucks "The Surge"](https://Adsoftheworld.com/campaigns/volvo-trucks-the-surge)
- [Automotive World — lançamento ao vivo da nova Scania](https://www.automotiveworld.com/news-releases/birth-new-scania-near-watch-live/)
- [Superbien — Scania "Driving the Shift"](https://www.superbien.studio/projects/scania-driving-the-shift)
