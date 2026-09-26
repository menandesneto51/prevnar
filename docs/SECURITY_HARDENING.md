# PREVNAR — Hardening e configuração segura

## APIs mutáveis

As rotas:
- `POST /api/carga-situacao1`;
- `POST /api/rebuild-mart`

são administrativas.

### GitHub Pages

No deploy público atual, `web/src/app/api` é removido antes do build. Portanto, a publicação é somente leitura.

### Desenvolvimento local

Em ambiente não produtivo, chamadas sem token são aceitas **somente em loopback** (`localhost`, `127.0.0.1`, `::1`).

Para exigir token também localmente:

```bash
PREVNAR_REQUIRE_LOCAL_TOKEN=1
PREVNAR_API_TOKEN=<segredo>
```

### Deploy server-side

Obrigatório configurar:

```bash
PREVNAR_API_TOKEN=<segredo forte>
PREVNAR_SERVER_SIDE_DEPLOY=1
```

O token é aceito por:
- `Authorization: Bearer ...`;
- `X-API-Key: ...`.

Não inserir o token no frontend público.

## Upload Situação 1

Controles atuais:
- chave de condição em allowlist;
- extensão CSV;
- limite de 2 MB;
- máximo de 10.000 linhas;
- colunas obrigatórias `uf,elegiveis`;
- UF válida;
- UF não duplicada;
- elegíveis inteiro não negativo;
- escrita somente após validação;
- nome de destino controlado pelo servidor.

## Python

A resolução ocorre nesta ordem:

1. `PREVNAR_PYTHON`;
2. `.venv/Scripts/python.exe`;
3. `.venv/bin/python`;
4. `python` no Windows ou `python3` em Unix.

## TLS

A validação TLS nunca deve ser desabilitada.

Se a rede institucional utilizar proxy/inspeção TLS, configurar a CA confiável:

```bash
PREVNAR_CA_BUNDLE=/caminho/ca-institucional.pem
```

O arquivo de CA não deve ser versionado quando contiver material interno não publicável.

## Segredos

Segredos devem ficar:
- em variáveis de ambiente;
- secret store do ambiente;
- GitHub Actions Secrets quando aplicável.

Nunca em:
- código;
- JSON público;
- frontend;
- commits;
- logs.

## Verificação

Para deploy server-side:

```bash
PREVNAR_SERVER_SIDE_DEPLOY=1 python etl/release_guardian.py --mode release
```
