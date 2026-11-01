import type { Metadata } from 'next';
import { Barlow, Barlow_Condensed } from 'next/font/google';
import './globals.css';
import { CarrinhoProvider } from '@/components/Carrinho';
import { Rastreio } from '@/components/Rastreio';

const sans = Barlow({ subsets: ['latin'], weight: ['400', '500', '600', '700'], variable: '--fonte-sans' });
const display = Barlow_Condensed({ subsets: ['latin'], weight: ['600', '700', '800'], variable: '--fonte-display' });

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'),
  title: { default: 'Maracá Diesel | Peças e serviços para caminhões', template: '%s | Maracá Diesel' },
  description: 'Peças e serviços para caminhões em um só lugar. Catálogo online, compra com login Google ou Face ID e orçamento rápido pelo WhatsApp.',
  openGraph: { type: 'website', locale: 'pt_BR', siteName: 'Maracá Diesel' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${sans.variable} ${display.variable}`}>
      <body><CarrinhoProvider>{children}<Rastreio /></CarrinhoProvider></body>
    </html>
  );
}
