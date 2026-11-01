'use client';
import { useEffect } from 'react';
import { animate, onScroll, stagger } from 'animejs';

/** Revela .js-rev e grades .js-cards ao rolar (padrão "reveal" das peças de lançamento de caminhões). */
export function Revela() {
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const anims = [...document.querySelectorAll<HTMLElement>('.js-rev')].map((el) =>
      animate(el, { opacity: [0, 1], y: [32, 0], duration: 800, ease: 'outQuint', autoplay: onScroll({ target: el, enter: 'bottom-=80 top' }) }));
    document.querySelectorAll<HTMLElement>('.js-cards').forEach((g) => {
      anims.push(animate(g.children, { opacity: [0, 1], y: [48, 0], duration: 900, delay: stagger(90), ease: 'outQuint', autoplay: onScroll({ target: g, enter: 'bottom-=60 top' }) }));
    });
    return () => anims.forEach((a) => a.revert());
  }, []);
  return null;
}
