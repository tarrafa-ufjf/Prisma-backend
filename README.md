# Instalação

primeiramente rode o comando para inicializar os bancos e serviços com o docker

```bash
docker compose up -d
```

Após isso, Entre no diretório **worker** e rode os comando:

```bash
poetry install
```

```bash
poetry run python install.py
```

**Observação:** Pretendemos, futuramente, simplificar todos os processos utilizando um arquivo bash.