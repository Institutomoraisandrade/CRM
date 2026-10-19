# Skills

Estas skills vêm do projeto [Superpowers](https://github.com/obra/superpowers)
(Jesse Vincent / Prime Radiant, licença MIT — ver `LICENSE-superpowers.txt`).

Elas implementam uma metodologia de desenvolvimento de software para agentes
Claude Code: brainstorming → design → git worktree → plano de tarefas → TDD →
revisão de código → merge/PR. Usamos essas skills para desenvolver o CRM do
Instituto Morais Andrade dentro deste repositório.

Fluxo básico (ver README original do Superpowers para detalhes de cada skill):

1. **brainstorming** — refina a ideia em um design, com perguntas.
2. **using-git-worktrees** — cria workspace isolado numa branch nova.
3. **writing-plans** — quebra o trabalho em tarefas pequenas e verificáveis.
4. **subagent-driven-development** / **executing-plans** — implementa o plano.
5. **test-driven-development** — RED-GREEN-REFACTOR.
6. **requesting-code-review** — revisão entre tarefas.
7. **finishing-a-development-branch** — decide merge/PR e limpa o worktree.
