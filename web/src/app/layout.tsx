import type { Metadata } from "next";
import { Nav } from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Radar Vacinal · VPC20 CRIE",
  description: "Painel de oportunidade de vacinação VPC20 nos CRIEs — NT 52/2026",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">
        <Nav />
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        <footer className="site-footer mt-8">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 text-xs text-white/90">
            <div>
              Radar Vacinal · Painel de oportunidade (não cobertura %), exceto Situação 1 com
              cadastro. Referência: NT 52/2026-CGICI/DPNI/SVSA/MS.
            </div>
            <div className="flex items-center gap-3 opacity-95">
              <span>JAMBRO</span>
              <span aria-hidden>·</span>
              <span>IPADS</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
