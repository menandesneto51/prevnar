"""Gera PDF comparativo: escopo inicial vs implementado vs pendente vs inviável."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from paths import MART, REF, ROOT

OUT_DIR = ROOT / "docs"
OUT_PDF = OUT_DIR / "relatorio_implementacao_prevnar.pdf"
WEB_PDF = ROOT / "web" / "public" / "relatorio" / "relatorio_implementacao_prevnar.pdf"

FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_B = Path(r"C:\Windows\Fonts\arialbd.ttf")


def load_json(name: str, default=None):
    p = REF / name if (REF / name).exists() else MART / name
    if not p.exists():
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def status_label(st: str) -> str:
    return {
        "ok": "Implementado",
        "parcial": "Parcial",
        "sem_dado": "Sem dado",
        "planejado": "Pendente",
    }.get(st, st)


PENDENTE = [
    ("CKAN jun/jul 2026", "Ampliar numerador além de mai/2026", "etl/run_ckan_pipeline.py"),
    ("Cadastros Situação 1 oficiais", "Substituir seeds por SICLOM/ABTO/SBN etc.", "data/manual/situacao1/"),
    ("CNES CRIE definitivo", "Lista seed não bate API; % fora CRIE = 100%", "data/reference/cnes_crie.json"),
    ("Mapa municipal vacinados", "por_municipio vazio no mart atual", "numerador CKAN multi-mês"),
    ("SINAN/SIH/SIM FTP", "Automatizar PySUS/DATASUS (hoje seeds 27 UFs)", "etl/extract_nacional.py"),
    ("SIES VPC20 na API", "API agrega pneumo 10/13; VPC20 não discrimina", "extract_sies"),
    ("ESAVI completo", "API vazia; seed manual 5 registros", "data/manual/templates/esavi_template.csv"),
]

INVIAVEL = [
    (
        "CID motivo_indicacao (PNI 2026)",
        "CSV CKAN 2026 não traz coluna CID; REST também não. Cobertura Sit.1 "
        "definitiva por condição clínica não é possível só com bases abertas atuais.",
    ),
    (
        "Cobertura Sit.1 para todas NT52",
        "Denominadores oficiais por condição (21 grupos) não existem em API única; "
        "requer cadastros manuais/parceiros por fonte (SICLOM, ABTO, REBRAFC…).",
    ),
    (
        "Inferência causal desfecho",
        "SINAN/SIH/SIM/SRAG × VPC20 são indicadores ecológicos; dashboard documenta "
        "limitação — não há desenho observacional individual.",
    ),
    (
        "Numerador 100% CRIE via PNI aberto",
        "Grande parte VPC20 mai/2026 é grupo 000210 (Faixa Etária / privado), "
        "fora do recorte CRIE/RIE estrito sem bases complementares.",
    ),
    (
        "SIES dose a dose VPC20",
        "OpenDataSUS SIES não expõe classe VPC20 de forma confiável; proxy pneumo total.",
    ),
]


def build_sections() -> dict:
    plano = load_json("plano_extracao_nacional.json", {})
    indicadores = load_json("indicadores_nacionais.json", {"indicadores": []})
    nacional = load_json("nacional.json", {})
    kpis = nacional.get("kpis") or {}
    status_rows = nacional.get("indicadores_status") or []

    fontes_plano = plano.get("fontes") or []
    abas_plano = plano.get("dashboard_nacional_abas") or []
    ind_catalog = indicadores.get("indicadores") or []

    impl_abas = [
        ("/", "Nacional — KPIs oportunidade"),
        ("/indicadores", "Catálogo 20 indicadores + status"),
        ("/regioes", "Gap por região de saúde"),
        ("/serie", "Transição pneumocócica VPC10/13/20"),
        ("/monitoramento", "SINAN · SIH · SIM · SRAG"),
        ("/estoque", "SIES distribuídas vs aplicadas"),
        ("/custo", "Custo do gap BPS + IPCA"),
        ("/qualidade", "Atraso RNDS · ESAVI · oferta CRIE"),
        ("/condicoes", "Gap por condição NT52"),
        ("/ufs", "Drill-down UF"),
        ("/carga", "Upload cadastros Situação 1"),
    ]

    etl_scripts = sorted(p.name for p in (ROOT / "etl").glob("*.py"))

    counts = {"ok": 0, "parcial": 0, "sem_dado": 0, "planejado": 0}
    for r in status_rows:
        counts[r.get("status", "?")] = counts.get(r.get("status", "?"), 0) + 1

    return {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "baseline": {
            "plano": "data/reference/plano_extracao_nacional.json",
            "indicadores": "data/reference/indicadores_nacionais.json",
            "extracao_md": "data/reference/EXTRACAO_NACIONAL.md",
            "n_fontes": len(fontes_plano),
            "n_indicadores": len(ind_catalog),
            "n_abas_plano": len(abas_plano),
        },
        "kpis": kpis,
        "indicadores_status": status_rows,
        "counts": counts,
        "fontes_plano": fontes_plano,
        "abas_plano": abas_plano,
        "abas_impl": impl_abas,
        "etl_scripts": etl_scripts,
        "pendente": PENDENTE,
        "inviavel": INVIAVEL,
    }


def write_markdown(data: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / "relatorio_implementacao_prevnar.md"
    lines = [
        "# Radar Vacinal VPC20 · Relatório de implementação",
        "",
        f"Gerado em: {data['gerado_em']}",
        "",
        "## Documento baseline (início do projeto)",
        "",
        f"- Plano de extração: `{data['baseline']['plano']}`",
        f"- Catálogo de indicadores: `{data['baseline']['indicadores']}`",
        f"- {data['baseline']['n_fontes']} fontes planejadas · "
        f"{data['baseline']['n_indicadores']} indicadores · "
        f"{data['baseline']['n_abas_plano']} abas no plano inicial",
        "",
        "## KPIs atuais (mart nacional)",
        "",
        f"| KPI | Valor |",
        f"|-----|-------|",
        f"| Elegíveis | {data['kpis'].get('elegiveis', '—'):,} |".replace(",", ".") if isinstance(data['kpis'].get('elegiveis'), int) else f"| Elegíveis | {data['kpis'].get('elegiveis', '—')} |",
        f"| Vacinados VPC20 | {data['kpis'].get('pessoas_vacinadas_vpc20', '—'):,} |".replace(",", ".") if isinstance(data['kpis'].get('pessoas_vacinadas_vpc20'), int) else "",
        f"| Gap | {data['kpis'].get('gap_absoluto', '—'):,} |".replace(",", ".") if isinstance(data['kpis'].get('gap_absoluto'), int) else "",
        f"| Custo gap (BRL) | {data['kpis'].get('custo_gap_brl', '—')} |",
        f"| Fonte numerador | {data['kpis'].get('fonte_numerador', '—')} |",
        "",
        "## Indicadores (baseline → status atual)",
        "",
        "| ID | Nome | Família | Status | Valor |",
        "|----|------|---------|--------|-------|",
    ]
    for r in data["indicadores_status"]:
        val = r.get("valor")
        if isinstance(val, float):
            val = round(val, 2)
        lines.append(
            f"| {r.get('id')} | {r.get('nome')} | {r.get('familia')} | "
            f"**{status_label(r.get('status', ''))}** | {val} |"
        )
    lines += [
        "",
        f"**Resumo:** {data['counts'].get('ok', 0)} ok · "
        f"{data['counts'].get('parcial', 0)} parcial · "
        f"{data['counts'].get('sem_dado', 0)} sem dado",
        "",
        "## Páginas do painel (plano vs implementado)",
        "",
    ]
    for rota, foco in data["abas_impl"]:
        lines.append(f"- `{rota}` — {foco}")
    lines += ["", "## Pendências", ""]
    for item, desc, ref in data["pendente"]:
        lines.append(f"- **{item}**: {desc} (`{ref}`)")
    lines += ["", "## Limitações / não alcançável com bases atuais", ""]
    for tit, desc in data["inviavel"]:
        lines.append(f"- **{tit}**: {desc}")
    lines += ["", "## Scripts ETL", "", ", ".join(f"`{s}`" for s in data["etl_scripts"])]
    md.write_text("\n".join(lines), encoding="utf-8")
    return md


def write_pdf(data: dict) -> Path:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise SystemExit("Instale: .venv\\Scripts\\pip install fpdf2") from exc

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    if FONT.exists():
        pdf.add_font("Arial", "", str(FONT))
        pdf.add_font("Arial", "B", str(FONT_B))
        family = "Arial"
    else:
        family = "Helvetica"

    def h1(t: str):
        pdf.set_font(family, "B" if FONT.exists() else "", 14)
        pdf.multi_cell(0, 8, t)
        pdf.ln(2)

    def h2(t: str):
        pdf.set_font(family, "B" if FONT.exists() else "", 11)
        pdf.multi_cell(0, 7, t)
        pdf.ln(1)

    def body(t: str):
        pdf.set_font(family, "", 9)
        pdf.multi_cell(0, 5, t)
        pdf.ln(1)

    def row(cols: list[str], widths: list[int], bold=False):
        pdf.set_font(family, "B" if bold and FONT.exists() else "", 8)
        for txt, w in zip(cols, widths):
            pdf.cell(w, 6, (txt or "")[:48], border=1)
        pdf.ln()

    pdf.add_page()
    h1("Radar Vacinal VPC20 · CRIE")
    body("Relatorio comparativo de implementacao")
    body(f"Gerado: {data['gerado_em']}")
    pdf.ln(3)

    h2("1. Baseline (documento inicial)")
    body(
        f"Plano: {data['baseline']['plano']}\n"
        f"Indicadores: {data['baseline']['indicadores']}\n"
        f"{data['baseline']['n_fontes']} fontes · "
        f"{data['baseline']['n_indicadores']} indicadores · "
        f"{data['baseline']['n_abas_plano']} abas planejadas"
    )

    h2("2. KPIs atuais")
    k = data["kpis"]
    for label, key in [
        ("Elegiveis", "elegiveis"),
        ("Vacinados VPC20", "pessoas_vacinadas_vpc20"),
        ("Gap", "gap_absoluto"),
        ("Custo gap BRL", "custo_gap_brl"),
        ("Fonte numerador", "fonte_numerador"),
        ("Sem CID na fonte", "sem_cid_na_fonte"),
    ]:
        body(f"  {label}: {k.get(key, '—')}")

    h2("3. Indicadores — baseline vs status")
    c = data["counts"]
    body(f"Resumo: {c.get('ok', 0)} ok | {c.get('parcial', 0)} parcial | {c.get('sem_dado', 0)} sem dado")
    widths = [38, 52, 28, 22, 22]
    row(["ID", "Nome", "Familia", "Status", "Valor"], widths, bold=True)
    for r in data["indicadores_status"]:
        val = r.get("valor")
        if isinstance(val, float):
            val = round(val, 2)
        row(
            [
                str(r.get("id", "")),
                str(r.get("nome", ""))[:40],
                str(r.get("familia", "")),
                status_label(str(r.get("status", ""))),
                str(val),
            ],
            widths,
        )

    pdf.add_page()
    h2("4. Painel web implementado")
    for rota, foco in data["abas_impl"]:
        body(f"  {rota} — {foco}")

    h2("5. Pendencias")
    for item, desc, ref in data["pendente"]:
        body(f"  • {item}: {desc} [{ref}]")

    h2("6. Limitacoes / inviavel")
    for tit, desc in data["inviavel"]:
        body(f"  • {tit}: {desc}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PDF))
    WEB_PDF.parent.mkdir(parents=True, exist_ok=True)
    WEB_PDF.write_bytes(OUT_PDF.read_bytes())
    return OUT_PDF


def main() -> None:
    data = build_sections()
    md = write_markdown(data)
    pdf = write_pdf(data)
    (OUT_DIR / "relatorio_implementacao_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Markdown: {md}")
    print(f"PDF: {pdf}")


if __name__ == "__main__":
    main()
