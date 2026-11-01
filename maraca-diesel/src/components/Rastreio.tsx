'use client';
import Script from 'next/script';
import { useEffect, useState } from 'react';

declare global { interface Window { fbq?: (...a: unknown[]) => void; gtag?: (...a: unknown[]) => void; dataLayer?: unknown[] } }

/** Evento no navegador (Pixel + GA4). Mesmo eventId do servidor → a Meta deduplica. */
export function rastreia(evento: string, dados: Record<string, unknown> = {}, eventId?: string) {
  window.fbq?.('track', evento, dados, eventId ? { eventID: eventId } : undefined);
  const ga: Record<string, string> = { Lead: 'generate_lead', ViewContent: 'view_item', AddToCart: 'add_to_cart', InitiateCheckout: 'begin_checkout', Purchase: 'purchase', CompleteRegistration: 'sign_up' };
  window.gtag?.('event', ga[evento] ?? evento, dados);
}
export const novoEventId = () => (crypto.randomUUID?.() ?? String(Date.now()));

/** Banner LGPD: os pixels de remarketing só carregam após consentimento. */
export function Rastreio() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => { const m = document.cookie.match(/md_consent=(sim|nao)/); setOk(m ? m[1] === 'sim' : null); }, []);
  const decide = (v: boolean) => { document.cookie = `md_consent=${v ? 'sim' : 'nao'}; max-age=${60 * 60 * 24 * 180}; path=/; samesite=lax`; setOk(v); };
  const pixel = process.env.NEXT_PUBLIC_META_PIXEL_ID, ga = process.env.NEXT_PUBLIC_GA4_ID;
  return (
    <>
      {ok && pixel && (
        <Script id="pixel" strategy="afterInteractive">{`!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','${pixel}');fbq('track','PageView');`}</Script>
      )}
      {ok && ga && (<>
        <Script src={`https://www.googletagmanager.com/gtag/js?id=${ga}`} strategy="afterInteractive" />
        <Script id="ga4" strategy="afterInteractive">{`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','${ga}');`}</Script>
      </>)}
      {ok === null && (
        <div role="dialog" aria-label="Cookies" className="fixed inset-x-3 bottom-3 z-50 mx-auto max-w-2xl rounded-md bg-marinho p-4 text-white shadow-2xl md:flex md:items-center md:gap-4">
          <p className="text-sm">Usamos cookies para medir o site e mostrar ofertas de peças relevantes para você (remarketing). <a className="underline" href="/privacidade">Política de privacidade</a>.</p>
          <div className="mt-3 flex shrink-0 gap-2 md:mt-0">
            <button className="btn btn-contorno h-10 px-4 text-sm" onClick={() => decide(false)}>Recusar</button>
            <button className="btn btn-sinal h-10 px-4 text-sm" onClick={() => decide(true)}>Aceitar</button>
          </div>
        </div>
      )}
    </>
  );
}
