import { Topo } from '@/components/Topo';
export const metadata = { title: 'Privacidade' };
export default function Pagina() {
  return (<><Topo /><main className="prose mx-auto max-w-3xl px-5 py-14">
    <h1 className="titulo">Política de privacidade</h1>
    <p className="mt-6">[Texto jurídico a validar] Coletamos nome, e-mail e telefone para responder orçamentos e processar pedidos (base legal: execução de contrato). Com seu consentimento, usamos cookies e dados de navegação para mostrar anúncios relevantes (Meta, Google). Você pode revogar o consentimento a qualquer momento apagando os cookies ou pedindo a exclusão pelo e-mail do encarregado (DPO).</p>
  </main></>);
}
