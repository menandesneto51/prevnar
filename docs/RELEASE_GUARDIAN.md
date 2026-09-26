# PREVNAR — Release Guardian

## Finalidade

O Release Guardian transforma parte das regras de governança do PREVNAR em verificações automáticas.

Ele **não substitui** validação epidemiológica, jurídica, de privacidade ou institucional.

## Modos

### CI

```bash
python etl/release_guardian.py --mode ci
```

Valida estrutura, evidência e segurança. Metadados runtime ainda ausentes geram warning quando possível.

### Release

```bash
python etl/release_guardian.py --mode release
```

Modo mais estrito. Deve ser usado após reconstrução dos marts e antes de uma publicação institucional.

## Gates implementados

- registro legal válido;
- source registry válido;
- catálogo de indicadores versionado;
- `decision_grade` obrigatório;
- E5 proibido como decision-grade;
- freshness de fontes críticas;
- fixture ativa;
- detecção básica de segredos;
- detecção de CPF válido;
- detecção contextual de CNS;
- rotas mutáveis sem autenticação;
- geração de relatório estruturado.

## Relatório

O resultado é gravado em:

`data/mart/_meta/release_guardian.json`

## Rotas server-side

No deploy estático do GitHub Pages, as rotas `web/src/app/api` são removidas.

Se o PREVNAR for implantado server-side, executar o Guardian com:

```bash
PREVNAR_SERVER_SIDE_DEPLOY=1 python etl/release_guardian.py --mode release
```

Nesse cenário, rotas mutáveis sem autenticação passam a ser erro bloqueante.

## Limitações

Scanners automáticos podem gerar falsos positivos e não substituem:
- secret scanning nativo;
- SAST/DAST;
- avaliação LGPD;
- revisão humana;
- pentest;
- validação de infraestrutura.
