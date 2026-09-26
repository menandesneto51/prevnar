# PREVNAR · Inteligência Vacinal

Plataforma em evolução para **monitoramento, qualidade, oportunidade e inteligência em imunização**, atualmente com implementação inicial centrada em **VPC20 / RIE / CRIE**.

> Estado da evolução: **PREVNAR v2.0 — governança e generalização em andamento**.

## O que existe hoje

- pipeline Python + DuckDB;
- numeradores de vacinação;
- denominadores por diferentes estratégias;
- marts analíticos;
- indicadores nacionais, UF, região de saúde e município;
- monitoramento de qualidade;
- integração de fontes como PNI, IBGE, CNES, SIES, ESAVI e bases de desfecho;
- dashboard Next.js;
- mapas Leaflet;
- export estático para GitHub Pages;
- geração de relatório.

## Estrutura

- `etl/` — extração, transformação, qualidade e construção de marts
- `web/` — dashboard Next.js
- `data/reference/` — metadados, regras e referências
- `data/raw/` — dados brutos locais; não versionar bases sensíveis
- `data/manual/` — cargas administrativas controladas
- `data/mart/` — agregados consumidos pelo painel
- `docs/` — documentação metodológica, jurídica e operacional
- `.cursor/rules/` — regras persistentes de implementação no Cursor
- `AGENTS.md` — arquitetura de agentes PREVNAR

## Governança v2

Antes de alterar indicadores, fontes ou regras vacinais, consultar:

1. [Governança legal](docs/GOVERNANCA_LEGAL.md)
2. [Metodologia e níveis de evidência](docs/METODOLOGIA_EVIDENCIA.md)
3. [Governança de dados e LGPD](docs/GOVERNANCA_DADOS_LGPD.md)
4. [Registro de fontes e proveniência](docs/REGISTRO_FONTES_E_PROVENIENCIA.md)
5. [Triagem de RIPD](docs/RIPD_TRIAGEM.md)
6. [Checklist de conformidade](docs/CHECKLIST_CONFORMIDADE.md)
7. [Roadmap v2](docs/ROADMAP_V2.md)
8. [Arquitetura de agentes](AGENTS.md)

Registro normativo estruturado: `docs/legal_register.json`.

Motor vacinal:
- `data/reference/vaccine_registry.json`;
- `data/reference/normative_rules.json`;
- `etl/vaccine_rules.py`;
- [onboarding de novo imunobiológico](docs/ONBOARDING_IMUNOBIOLOGICO.md).

## Princípio metodológico

O PREVNAR distingue:

- **E1 — observado confirmado**
- **E2 — observado por proxy**
- **E3 — estimado**
- **E4 — manual validado**
- **E5 — demonstrativo**

Proxy, estimativa e fixture não podem ser apresentados como observação equivalente.

O conceito de **gap de pessoas únicas** somente deve ser utilizado quando houver possibilidade válida de deduplicação da população elegível. A soma de elegíveis por múltiplas condições deve ser tratada como **oportunidades estimadas**, pois pode haver sobreposição entre indivíduos.

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r etl\requirements.txt
.venv\Scripts\python etl\build_mart.py

cd web
npm install
npm run dev
```

Abra http://localhost:3000

## Numerador VPC20

Ordem atual: **CSV** em `data/raw/` → **API** → fixture/demonstração.

```bash
.\.venv\Scripts\python etl\numerador.py --source api
.\.venv\Scripts\python etl\numerador.py --source csv
.\.venv\Scripts\python etl\build_mart.py
```

A fonte aberta atual pode não disponibilizar CID/motivo de indicação. Nessa situação, breakdown clínico baseado em grupos auxiliares deve ser explicitamente marcado como **proxy (E2)**.

## Dashboard

Rotas principais:

- `/` — visão nacional
- `/indicadores`
- `/regioes`
- `/serie`
- `/monitoramento`
- `/estoque`
- `/custo`
- `/qualidade`
- `/condicoes`
- `/ufs`
- `/carga` — somente ambiente controlado/server-side

## Cursor e agentes

O **Cursor é o ambiente padrão de continuidade técnica**.

Ordem dos agentes:

```
Data
→ Epidemiology
→ Data Quality
→ Legal & Privacy
→ Intelligence
→ Action
→ Release Guardian
```

Ver `AGENTS.md` e `.cursor/rules/`.

## Segurança

- nunca versionar CPF, CNS, nome ou dados clínicos individualizados;
- nunca versionar tokens/senhas;
- endpoints mutáveis exigem autenticação antes de exposição externa;
- não usar `verify=False` como solução permanente;
- toda publicação deve passar por quality/privacy/release gates.

## Documentação completa

Ver [docs/README.md](docs/README.md).
