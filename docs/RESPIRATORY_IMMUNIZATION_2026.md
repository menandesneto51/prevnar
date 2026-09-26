# PREVNAR — Imunização respiratória 2026

**Versão:** 1.0  
**Data:** 26/09/2026  
**Escopo:** VVSR materna, nirsevimabe, influenza e covid-19.

## 1. Objetivo

Criar uma camada comum de inteligência para prevenção de doença respiratória grave, mantendo separadas:

- imunização materna;
- imunização passiva infantil;
- vacinação de rotina/campanha;
- registro;
- oportunidade;
- cobertura;
- segurança;
- desfechos epidemiológicos.

O PREVNAR não deve tratar todos esses produtos como se fossem a mesma intervenção.

## 2. Situação de onboarding

| Imunobiológico | Tipo | Regra clínica | Dados PNI | Monitoramento |
|---|---|---|---|---|
| VVSR materna | vacina | estruturada/ativa | mapeamento pendente | ainda não automatizado |
| nirsevimabe | anticorpo monoclonal | estruturada/ativa | mapeamento pendente | ainda não automatizado |
| influenza | vacina | draft | mapeamento pendente | não ativado |
| covid-19 | vacina | draft | mapeamento por produto/faixa pendente | não ativado |

Ativar uma regra clínica não significa declarar que a fonte de dados já está pronta para indicadores de cobertura.

## 3. VVSR materna

### Regra estruturada

- gestante;
- a partir da 28ª semana gestacional;
- sem restrição de idade materna;
- uma dose em cada gestação;
- pode ser administrada concomitantemente com outras vacinas previstas para a gestante.

### Dose administrada antes da 28ª semana

Não repetir a dose apenas por ter sido administrada precocemente.

O PREVNAR retorna:

`do_not_repeat_routine_dose`

e registra motivo específico para monitoramento.

### Dados necessários para monitoramento

Numerador:
- dose VVSR;
- gestação;
- idade gestacional no momento da dose;
- município/estabelecimento;
- data.

Denominadores possíveis:
- SINASC/NV;
- e-SUS APS/pré-natal;
- SISAB/produção;
- estimativas gestacionais, quando necessário.

A definição oficial de cobertura deve respeitar numerador e denominador compatíveis.

## 4. Nirsevimabe

### Tipo

Anticorpo monoclonal — imunização passiva.

### Prematuridade

Elegibilidade estruturada:
- idade gestacional ao nascer ≤ 36 semanas e 6 dias;
- idade cronológica < 6 meses.

A estratégia é tratada como **ao longo de todo o ano** para prematuros elegíveis.

### Comorbidades

Elegibilidade estruturada:
- criança < 24 meses;
- presença de comorbidade elegível conforme protocolo oficial.

O caminho por comorbidade observa sazonalidade do VSR.

### Dose estruturada

Primeira sazonalidade:
- peso < 5 kg → 50 mg;
- peso ≥ 5 kg → 100 mg.

Segunda sazonalidade para criança elegível por comorbidade:
- 200 mg;
- duas injeções de 100 mg.

### Segurança

O registro normativo impede interpretação de duas seringas de 50 mg como substituição automática de uma dose de 100 mg.

## 5. Influenza

Entidade cadastrada, mas regra permanece `draft`.

A NT nº 24/2026 orienta o registro de doses aplicadas em 2026.

Antes de ativar o motor:
- mapear código(s) do imunobiológico;
- mapear estratégia/campanha/rotina;
- definir grupos de interesse;
- versionar a sazonalidade;
- validar regras de dose por idade/histórico quando aplicáveis.

## 6. Covid-19

Entidade cadastrada, mas regra permanece `draft`.

A NT nº 91/2026-DPNI/SVSA/MS deve ser utilizada no contexto de transição operacional e segurança do produto Comirnaty Refrigerada cepa LP.8.1.

Não criar uma regra única genérica de covid-19 sem separar:
- produto;
- faixa etária;
- histórico de doses;
- condição especial;
- vigência;
- estratégia.

## 7. Fontes de dados

### Imunização

- PNI/OpenDataSUS;
- RNDS/RIA;
- bases institucionais autorizadas.

### Gestação/nascimento

- SINASC;
- e-SUS APS;
- SISAB;
- bases de pré-natal autorizadas.

### Desfechos respiratórios

- SIVEP-Gripe/SRAG;
- SIH;
- SIM;
- vigilância laboratorial.

## 8. Indicadores candidatos

### VVSR materna

- gestantes vacinadas;
- doses por município;
- oportunidade a partir da 28ª semana;
- atraso entre elegibilidade e dose;
- doses administradas antes da 28ª semana;
- completude de informação gestacional;
- distribuição territorial.

### Nirsevimabe

- crianças imunizadas;
- prematuros elegíveis imunizados;
- crianças com comorbidade elegível imunizadas;
- distribuição por peso/dose;
- uso por sazonalidade;
- oportunidade na maternidade;
- perdas de oportunidade;
- divergências de dose;
- administração por CRIE/maternidade.

### Respiratórios

- SRAG por VSR;
- internações;
- mortalidade;
- positividade laboratorial;
- pressão hospitalar.

## 9. Regra analítica

Desfechos respiratórios e vacinação/imunização podem ser analisados em conjunto para vigilância populacional.

O PREVNAR **não deve concluir causalidade automaticamente** entre aumento/redução de cobertura e aumento/redução de SRAG, hospitalização ou óbito.

Qualquer análise de efetividade exige desenho epidemiológico adequado.

## 10. Próximos gates

Antes de ativar monitoramento automatizado de VVSR/nirsevimabe:

1. mapear códigos PNI;
2. validar códigos de dose/estratégia;
3. validar disponibilidade e completude;
4. definir denominador;
5. criar manifests/freshness;
6. adicionar indicadores ao catálogo;
7. criar testes;
8. validar interface;
9. executar Release Guardian.

Influenza e covid-19 exigem adicionalmente concluir suas regras normativas antes de saírem de `draft`.
