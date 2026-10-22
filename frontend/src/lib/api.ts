export class ApiError extends Error {
  status: number;
  constraint?: string;

  constructor(status: number, message: string, constraint?: string) {
    super(message);
    this.status = status;
    this.constraint = constraint;
  }
}

interface ValidationItem {
  loc?: (string | number)[];
  msg?: string;
}

function detailMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return (detail as ValidationItem[])
      .map((d) => `${(d.loc ?? []).filter((p) => p !== "body").join(".")}: ${d.msg ?? ""}`)
      .join("; ");
  }
  return `Помилка сервера (${status})`;
}

async function handle<T>(resp: Response): Promise<T> {
  const body = resp.headers.get("content-type")?.includes("json") ? await resp.json() : null;
  if (!resp.ok) throw new ApiError(resp.status, detailMessage(body, resp.status), body?.constraint ?? undefined);
  return body as T;
}

export async function apiGet<T>(path: string, params?: URLSearchParams): Promise<T> {
  const qs = params?.toString();
  return handle<T>(await fetch(qs ? `${path}?${qs}` : path));
}

export async function apiSend<T>(method: "POST" | "PATCH" | "DELETE", path: string, body?: unknown): Promise<T> {
  return handle<T>(await fetch(path, {
    method,
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  }));
}

export async function apiUpload<T>(path: string, files: File[]): Promise<T> {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  return handle<T>(await fetch(path, { method: "POST", body: form }));
}
