import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

// Renova a sessão do Supabase e guarda UTMs/click IDs (para remarketing e atribuição) por 90 dias.
export async function middleware(req: NextRequest) {
  let res = NextResponse.next({ request: req });
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) return res; // modo demonstração sem banco
  const supabase = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!, {
    cookies: {
      getAll: () => req.cookies.getAll(),
      setAll: (lista) => {
        lista.forEach(({ name, value }) => req.cookies.set(name, value));
        res = NextResponse.next({ request: req });
        lista.forEach(({ name, value, options }) => res.cookies.set(name, value, options));
      },
    },
  });
  const { data } = await supabase.auth.getUser();
  const p = req.nextUrl.searchParams;
  const chaves = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'];
  if (chaves.some((k) => p.has(k))) {
    const utm = Object.fromEntries(chaves.filter((k) => p.has(k)).map((k) => [k, p.get(k)]));
    res.cookies.set('md_utm', JSON.stringify(utm), { maxAge: 60 * 60 * 24 * 90, sameSite: 'lax', path: '/' });
    if (p.get('fbclid')) res.cookies.set('_fbc', `fb.1.${Date.now()}.${p.get('fbclid')}`, { maxAge: 60 * 60 * 24 * 90, path: '/' });
  }
  const protegidas = ['/conta', '/checkout', '/admin'];
  if (!data.user && protegidas.some((r) => req.nextUrl.pathname.startsWith(r))) {
    const url = req.nextUrl.clone(); url.pathname = '/entrar'; url.searchParams.set('volta', req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  return res;
}
export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|svg|webp|glb)$).*)'] };
