import 'server-only';
import { cookies, headers } from 'next/headers';
export async function contexto() {
  const h = await headers(), c = await cookies();
  let origem: Record<string, unknown> = {};
  try { origem = JSON.parse(c.get('md_utm')?.value ?? '{}'); } catch {}
  return {
    ip: h.get('x-forwarded-for')?.split(',')[0] ?? null, ua: h.get('user-agent'), referer: h.get('referer') ?? undefined,
    fbc: c.get('_fbc')?.value, fbp: c.get('_fbp')?.value, origem, consente: c.get('md_consent')?.value === 'sim',
  };
}
