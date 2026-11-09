# Identidade visual da FPS

Coloque aqui o **logo oficial** da Faculdade Pernambucana de Saúde:

| Arquivo | Uso | Obrigatório |
|---|---|---|
| `logo-fps.png` | rodapé dos slides (fundo branco) | sim |
| `logo-fps-branco.png` | capa, divisórias e encerramento (fundo escuro) | não — é gerado automaticamente |

Prefira PNG com fundo transparente e boa resolução (≥ 800 px de largura).
Depois de copiar o logo, rode a partir da pasta `trabalho-fps/`:

```bash
python3 scripts/extrair_cores_logo.py marca/logo-fps.png --salvar --gerar-negativo
```

O script lê as cores do logo, grava a paleta em `marca-fps.json` (garantindo contraste
de leitura) e cria a versão branca do logo. Se preferir as cores exatas do manual de marca da FPS,
edite `marca-fps.json` à mão (campos `primaria`, `secundaria`, `destaque`).

Enquanto o logo não for colocado, os slides usam um marcador de texto "FPS · Faculdade
Pernambucana de Saúde" e uma paleta provisória verde (estimada das fotos dos slides da disciplina).
