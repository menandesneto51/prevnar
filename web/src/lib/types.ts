export type EvidenceLevel = "E1" | "E2" | "E3" | "E4" | "E5";

export type CondicaoResumo = {
  condicao_id: number;
  condicao_nt52: string;
  situacao_denominador: number;
  elegiveis: number | null;
  elegiveis_display: string;
  pessoas_vacinadas: number;
  gap: number | null;
  cobertura_pct: number | null;
  exibe_cobertura: boolean;
  carga_pendente: boolean;
  raro?: boolean;
  gap_evidence_level?: string;
  gap_decision_grade?: boolean;
  gap_interpretation?: string;
};

export type UfResumo = {
  uf: string;
  elegiveis: number;
  oportunidades_estimadas: number;
  pessoas_vacinadas: number;
  pessoas_vacinadas_consolidado?: number;
  gap: number | null;
  gap_pessoas: number | null;
  gap_aproximado_legado?: number | null;
  pendencias: number;
};

export type GapLinha = {
  condicao_id: number;
  condicao_nt52: string;
  uf: string;
  elegiveis: number | null;
  elegiveis_display: string;
  elegiveis_suprimido?: boolean;
  pessoas_vacinadas: number;
  gap: number | null;
  cobertura_pct: number | null;
  exibe_cobertura: boolean;
  situacao_denominador: number;
  carga_pendente: boolean;
  fonte_denominador?: string;
  raro?: boolean;
  numerator_evidence_level?: EvidenceLevel;
  denominator_evidence_level?: EvidenceLevel;
  gap_evidence_level?: string;
  gap_decision_grade?: boolean;
  clinical_match_confirmed?: boolean;
  gap_interpretation?: string;
};

export type MunResumo = {
  municipio_ibge: string;
  uf: string;
  nome?: string | null;
  pessoas_vacinadas: number;
  doses?: number;
};

export type DashboardData = {
  atualizado_em: string;
  nacional: {
    elegiveis: number;
    oportunidades_estimadas: number;
    pessoas_vacinadas: number;
    gap: number | null;
    gap_pessoas: number | null;
    gap_aproximado_legado?: number | null;
    gap_pessoas_disponivel?: boolean;
    nota_oportunidades?: string;
    taxa_cid_preenchido: number | null;
    total_doses: number;
    fixture?: boolean;
    fonte_numerador?: string;
    fonte_tipo?: string;
    sem_cid_na_fonte?: boolean;
    evidence_level_total?: EvidenceLevel;
    evidence_level_clinical_breakdown?: EvidenceLevel;
    decision_grade_clinical_breakdown?: boolean;
  };
  por_condicao: CondicaoResumo[];
  por_uf: UfResumo[];
  por_municipio?: MunResumo[];
  qualidade: {
    taxa_cid_preenchido: number | null;
    cids_nao_mapeados: Record<string, number>;
    filtro_crie_aplicado?: boolean;
    sem_cid_na_fonte?: boolean;
    fonte_tipo?: string;
    filtro_detalhe?: Record<string, unknown>;
    sanity_divergencia_pct: number | null;
    sanity_alerta: boolean;
    situacao1: {
      carregados: string[];
      pendentes: string[];
      detalhe: Record<string, number>;
    };
    nota_numerador?: string;
    freshness?: Record<
      string,
      {
        status?: "atual" | "atencao" | "desatualizado" | "desconhecido";
        source_id?: string;
        reference_period?: string | null;
        reference_end?: string | null;
        age_days?: number | null;
        attention_after_days?: number | null;
        stale_after_days?: number | null;
        critical_for_decision?: boolean;
      }
    >;
    freshness_alerta?: boolean;
  };
  provenance?: Record<string, unknown>;
  ufs: { uf: string; codigo_ibge: string; nome: string; regiao: string }[];
  condicoes: {
    condicao_id: number;
    condicao_nt52: string;
    situacao_denominador: number;
    exibe_cobertura: boolean;
    raro?: boolean;
  }[];
};
