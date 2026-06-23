from __future__ import annotations

JUDGE_DIMENSIONS = [
    "intencao_usuario",
    "aderencia_schema",
    "precisao_semantica",
    "seguranca",
    "completude",
    "robustez",
    "ausencia_ambiguidades",
]

MOODLE_RULES = """
Você é um especialista em SQL e no schema do Moodle. Ao gerar SQLs, siga rigorosamente:

1) Entenda a intenção do usuário antes de escrever qualquer cláusula.
2) Defina cada conceito (ex: 'curso' = mdl_course_categories; 'disciplina' = mdl_course).
3) Use unidades em escala humana (dias, não segundos), a menos que especificado.
4) Respeite limites dos dados: notas 0 <= nota <= 100.
5) Aprovação: média de notas igual ou acima de 69 nas disciplinas.
6) Consultas amplas NÃO usam LIMIT. Consultas com LIMIT OBRIGATORIAMENTE usam ORDER BY.
7) mdl_course_categories = curso (ex: Engenharia). mdl_course = disciplina/turma/oficina.
8) Tipos em mdl_grade_items: 'mod'=atividade, 'course'=nota final, 'category'=totalizador, 'block'=bloco.
9) mdl_user: deleted=1 são soft-deletes (manter para histórico, mas filtrar em consultas ativas).
10) mdl_course: id=1 é o site Moodle — excluir com `id != 1`. Filtrar visible=1 para publicados.
11) mdl_user_enrolments: matrícula ativa = status=0 AND (timeend=0 OR timeend > UNIX_TIMESTAMP()).
12) Na tabela mdl_context a coluna contextlevel representa: 10 é para sistema, 20 é para pessoal,
    30 é para usuários, 40 para course category, 60 para grupo, 70 para modulo, 80 para block
    e 50 é para cursos.

"""
