/** Records changed in this session keep a "fresh" mark until they are opened (per-viewer, session only). */
const KEY = "sims:fresh";

function read(): string[] {
  try {
    const value = JSON.parse(sessionStorage.getItem(KEY) ?? "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function write(ids: string[]): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(ids));
  } catch {
    /* storage unavailable: marks are a convenience only */
  }
}

export function markFresh(id: string): void {
  const ids = read();
  if (!ids.includes(id)) write([...ids, id]);
}

export function isFresh(id: string): boolean {
  return read().includes(id);
}

export function clearFresh(id: string): void {
  write(read().filter((x) => x !== id));
}
