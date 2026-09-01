/** Prefixo para assets estáticos (GitHub Pages: /prevnar). */
export const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

export function assetUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${basePath}${p}`;
}
