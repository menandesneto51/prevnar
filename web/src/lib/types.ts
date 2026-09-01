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
};

export type UfResumo = {
  uf: string;
  elegiveis: number;
  pessoas_vacinadas: number;
  pessoas_vacinadas_consolidado?: number;
  gap: number;
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
    pessoas_vacinadas: number;
    gap: number | null;
    taxa_cid_preenchido: number | null;
    total_doses: number;
    fixture?: boolean;
    fonte_numerador?: string;
    fonte_tipo?: string;
    sem_cid_na_fonte?: boolean;
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
  };
  ufs: { uf: string; codigo_ibge: string; nome: string; regiao: string }[];
  condicoes: {
    condicao_id: number;
    condicao_nt52: string;
    situacao_denominador: number;
    exibe_cobertura: boolean;
    raro?: boolean;
  }[];
};
