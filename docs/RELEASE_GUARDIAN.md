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
- política de benchmark regulatório válida;
- atos regulatórios referenciados com data de publicação disponível;
- Portaria GM/MS 5.663/2024 com publicação/vigência/provisões estruturadas;
- benchmark regulatório de 15 dias preservado como referência interna;
- papel atual do PREVNAR explicitamente analítico, sem declaração automática de infração;
- separação SIES público (distribuição) × SIES/DW institucional (estoque);
- proibição de inferir saldo atual a partir de doses distribuídas;
- proibição de seed SIES como dado observado;
- bloqueio de TLS sem verificação no extrator legado;
- contrato institucional com CPF/CNS proibidos;
- referências legais das regras resolvidas;
- regra ativa com vigência definida;
- regra ativa com escopo geográfico explícito;
- regra nacional com código BR;
- regra territorial com códigos de escopo;
- regra ativa com pelo menos um ato normativo;
- imunobiológico monitorado com código nacional;
- bloqueio de `monitored=true` quando o mapeamento de registro estiver incompleto/`pending`;
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
