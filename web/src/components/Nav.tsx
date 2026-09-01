"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Nacional" },
  { href: "/indicadores", label: "Indicadores" },
  { href: "/regioes", label: "Regiões" },
  { href: "/serie", label: "Série" },
  { href: "/monitoramento", label: "Monitoramento" },
  { href: "/estoque", label: "Estoque" },
  { href: "/custo", label: "Custo do gap" },
  { href: "/condicoes", label: "Condições" },
  { href: "/ufs", label: "UFs" },
  { href: "/qualidade", label: "Qualidade" },
  { href: "/relatorio", label: "Relatório" },
  { href: "/carga", label: "Carga Situação 1" },
];

export function Nav() {
  const pathname = usePathname();
  const crumb =
    links.find((l) => l.href === pathname)?.label ||
    links.find((l) => l.href !== "/" && pathname.startsWith(l.href))?.label ||
    "Painel";

  return (
    <header className="sticky top-0 z-40">
      <div className="site-header">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3">
          <Link href="/" className="flex min-w-0 flex-1 items-center gap-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/brand/logo-jambro.png"
              alt="JAMBRO"
              className="brand-logo"
              width={160}
              height={40}
            />
            <div className="hidden h-8 w-px bg-[var(--border)] sm:block" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/brand/logo-ipads.png"
              alt="IPADS"
              className="brand-logo"
              width={160}
              height={40}
            />
          </Link>
          <div className="text-right">
            <div className="text-sm font-semibold tracking-wide text-[var(--primary-deep)]">
              Radar Vacinal
            </div>
            <div className="text-xs text-[var(--muted)]">VPC20 · CRIE · NT 52/2026</div>
          </div>
        </div>
      </div>

      <nav className="site-nav">
        <div className="mx-auto flex max-w-7xl flex-wrap gap-1 px-4 py-2">
          {links.map((l) => {
            const active = pathname === l.href || (l.href !== "/" && pathname.startsWith(l.href));
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded-md px-3 py-1.5 text-sm transition ${
                  active
                    ? "bg-[var(--primary)] font-semibold text-white"
                    : "text-white/85 hover:bg-white/10 hover:text-white"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="site-breadcrumb">
        <div className="mx-auto max-w-7xl px-4 py-2 text-sm font-medium text-white">
          {crumb}
        </div>
      </div>
    </header>
  );
}
