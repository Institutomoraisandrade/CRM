import 'server-only';
export const rp = () => ({
  rpName: 'Maracá Diesel',
  rpID: process.env.WEBAUTHN_RP_ID ?? 'localhost',
  origin: process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000',
});
export const b64 = (u: Uint8Array) => Buffer.from(u).toString('base64url');
export const deB64 = (s: string) => new Uint8Array(Buffer.from(s, 'base64url'));
