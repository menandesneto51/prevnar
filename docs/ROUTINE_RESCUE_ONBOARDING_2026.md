# PREVNAR — Onboarding de vacinas de rotina, resgate e resposta 2026

**Versão:** 1.0  
**Data:** 26/09/2026

## Escopo

Este documento organiza o onboarding inicial de:

- HPV4;
- meningocócica ACWY;
- febre amarela;
- tríplice viral.

Nesta etapa, as quatro entidades permanecem em **draft** para regras clínicas/operacionais.

O objetivo é registrar corretamente:
- atos normativos;
- vigência;
- tipo de estratégia;
- contexto territorial;
- limites de interpretação.

## HPV4

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 32/2026-CGICI/DPNI/SVSA/MS.

A NT nº 32/2026 trata da inclusão de mulheres com NIC 2+ e AIS submetidas a procedimento excisional como grupo prioritário.

Antes de ativar regras:
- separar rotina;
- resgate;
- PrEP;
- grupos prioritários;
- esquema por grupo;
- faixa etária;
- códigos PNI;
- vigência específica.

## MenACWY

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 77/2025-CGICI/DPNI/SVSA/MS;
- NT nº 50/2026-CGICI/DPNI/SVSA/MS.

A NT nº 50/2026 descreve metodologia para avaliação de indicadores da população de 11 a 14 anos por coorte de nascimento.

**Não utilizar a NT nº 50/2026 como se fosse, isoladamente, regra de elegibilidade clínica.**

O PREVNAR deverá separar:
- regra de vacinação;
- cálculo de cobertura;
- coorte de nascimento;
- reforço;
- resgate.

## Febre amarela

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 6/2026-CGICI/DPNI/SVSA/MS.

A NT nº 6/2026 orienta a necessidade de dose padrão para pessoas que receberam dose fracionada na estratégia excepcional de 2018.

Esse cenário deve virar uma regra separada de:
- rotina;
- viajantes;
- bloqueio;
- áreas com recomendação;
- contraindicações/precauções.

Não generalizar automaticamente a regra de 2018 para outras situações.

## Tríplice viral / sarampo

Fontes iniciais:
- Calendário Nacional de Vacinação 2026;
- NT nº 98/2026-CGICI/DPNI/SVSA/MS;
- NT Conjunta nº 116/2026-DPNI/SVSA/MS.

A NT nº 98/2026 orienta dose zero em crianças.

O PREVNAR deve representar separadamente:
- rotina;
- dose zero;
- bloqueio;
- varredura;
- recomendação para viajantes;
- estratégias territoriais temporárias.

### Regra territorial obrigatória

Notas específicas para município/território **não podem** ser convertidas em regra nacional.

Campos futuros obrigatórios:

```json
{
  "geographic_scope": {
    "type": "national|state|municipality|polygon|facility",
    "codes": []
  }
}
```

### Regra temporal obrigatória

Estratégias temporárias devem possuir:

```json
{
  "effective_from": "YYYY-MM-DD",
  "effective_until": "YYYY-MM-DD"
}
```

Quando não houver data final explícita, a regra permanece sob revisão periódica e não deve ser assumida como permanente.

## Próxima etapa

1. mapear códigos oficiais PNI;
2. separar estratégia/rotina/campanha/bloqueio;
3. criar `data_plan`;
4. estruturar regras inequívocas;
5. testar limites de idade e vigência;
6. criar indicadores;
7. manter ações territoriais parametrizadas;
8. passar pelo Release Guardian.
