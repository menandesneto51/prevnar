import "server-only";

import { timingSafeEqual } from "crypto";
import { NextRequest, NextResponse } from "next/server";

const LOOPBACK = new Set(["localhost", "127.0.0.1", "::1"]);

function safeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  if (left.length !== right.length) return false;
  return timingSafeEqual(left, right);
}

function providedToken(req: NextRequest): string {
  const auth = req.headers.get("authorization") || "";
  if (auth.toLowerCase().startsWith("bearer ")) return auth.slice(7).trim();
  return (req.headers.get("x-api-key") || "").trim();
}

export function authorizeMutableRequest(req: NextRequest): NextResponse | null {
  const url = new URL(req.url);
  const localDev = process.env.NODE_ENV !== "production" && LOOPBACK.has(url.hostname);

  // Compatibilidade do fluxo local: somente loopback em ambiente não produtivo.
  if (localDev && process.env.PREVNAR_REQUIRE_LOCAL_TOKEN !== "1") return null;

  const expected = (process.env.PREVNAR_API_TOKEN || "").trim();
  if (!expected) {
    return NextResponse.json(
      {
        error:
          "API mutável desabilitada. Configure PREVNAR_API_TOKEN no servidor ou utilize o fluxo local em loopback.",
      },
      { status: 503 },
    );
  }

  const provided = providedToken(req);
  if (!provided || !safeEqual(provided, expected)) {
    return NextResponse.json({ error: "Não autorizado" }, { status: 401 });
  }
  return null;
}
