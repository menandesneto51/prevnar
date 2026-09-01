"""Orquestrador: extrações auxiliares + CKAN mai→jul + mart + nacional."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> None:
    etl = Path(__file__).resolve().parent
    os.chdir(etl)
    sys.path.insert(0, str(etl))

    ap = argparse.ArgumentParser(description="Pipeline completo Prevnar")
    ap.add_argument("--skip-ckan", action="store_true", help="Pula download CKAN (só rebuild)")
    ap.add_argument("--pni-pages", type=int, default=30, help="Novas páginas API PNI 2026")
    ap.add_argument("--aux-pages", type=int, default=10, help="Páginas SIES/SRAG/ESAVI")
    args = ap.parse_args()

    import extract_nacional

    print("\n=== 1/3 Extrações auxiliares ===", flush=True)
    extract_nacional.run(
        max_pages_aux=args.aux_pages,
        pni_cache_files=400,
        pni_fetch_pages=args.pni_pages,
    )

    if not args.skip_ckan:
        print("\n=== 2/3 Pipeline CKAN (mai→jul) ===", flush=True)
        import run_ckan_pipeline

        run_ckan_pipeline.main()
    else:
        print("\n=== 2/3 CKAN ignorado (--skip-ckan) ===", flush=True)
        os.environ["RADAR_NUMERADOR_SOURCE"] = "csv"
        import build_mart
        import build_nacional
        import numerador

        numerador.run(source="csv")
        build_mart.run(refresh_sources=False)
        build_nacional.build()

    print("\n=== 3/3 Concluído ===", flush=True)


if __name__ == "__main__":
    main()
