import type { Metadata } from "next";
import { Nav } from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "PREVNAR · Inteligência em Imunização",
  description: "Plataforma de inteligência, qualidade, oportunidade e monitoramento de imunização",
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
              PREVNAR · Inteligência em Imunização. Indicadores distinguem observação, proxy,
              estimativa e dados administrativos conforme sua evidência e proveniência.
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
