# AGENTS

## Registro obrigatorio de mudancas

Sempre que houver qualquer alteracao de codigo neste projeto, o agente deve atualizar o arquivo [`MUDANCAS_LOG.md`], que fica na raiz do repositorio.

Cada nova entrada no log deve incluir:

- data da mudanca, com horario;
- titulo curto;
- arquivos afetados;
- resumo objetivo do que mudou;
- impacto em relacao ao comportamento anterior, quando aplicavel.

## Regras

- O log deve ser atualizado na mesma tarefa em que o codigo for alterado.
- O log principal fica apenas na raiz do projeto.
- Nao criar logs paralelos em subpastas, salvo pedido explicito do usuario.
- Em mudancas pequenas, registrar de forma breve.
- Em refatoracoes ou mudancas de comportamento, registrar comparando antes e depois.
