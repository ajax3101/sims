/** Student register state as it lives in the URL, and its translation to the API query. */
export const FILTER_KEYS = [
  "q", "specialty_id", "program_id", "level", "form", "org_unit_id", "course", "group_id", "curator_id",
  "status", "funding", "has_academic_debt", "has_financial_debt",
] as const;
export type FilterKey = (typeof FILTER_KEYS)[number];

export const SORT_FIELDS = ["name", "group", "course", "status", "funding", "created_at", "financial_debt"] as const;
export const PAGE_SIZES = [25, 50, 100, 200] as const;

export interface StudentQuery {
  page: number;
  size: number;
  sort: string;
  filters: Partial<Record<FilterKey, string>>;
}

const DEFAULTS = { page: 1, size: 50, sort: "name" };

function isSort(value: string): boolean {
  return (SORT_FIELDS as readonly string[]).includes(value.replace(/^-/, ""));
}

export function parseStudentQuery(params: URLSearchParams): StudentQuery {
  const page = Number(params.get("page"));
  const size = Number(params.get("size"));
  const sort = params.get("sort") ?? "";
  const filters: StudentQuery["filters"] = {};
  for (const key of FILTER_KEYS) {
    const value = params.get(key);
    if (value) filters[key] = value;
  }
  return {
    page: Number.isInteger(page) && page >= 1 ? page : DEFAULTS.page,
    size: (PAGE_SIZES as readonly number[]).includes(size) ? size : DEFAULTS.size,
    sort: isSort(sort) ? sort : DEFAULTS.sort,
    filters,
  };
}

export function toApiParams(query: StudentQuery): URLSearchParams {
  const params = new URLSearchParams({ page: String(query.page), size: String(query.size), sort: query.sort });
  for (const [key, value] of Object.entries(query.filters)) {
    if (value && value.trim()) params.set(key, value.trim());
  }
  return params;
}

export function withFilter(query: StudentQuery, key: FilterKey, value: string): StudentQuery {
  const filters = { ...query.filters };
  if (value) filters[key] = value;
  else delete filters[key];
  return { ...query, page: 1, filters };
}

/** Clicking the sorted column flips direction; clicking another column sorts it ascending. */
export function nextSort(current: string, column: string): string {
  if (current === column) return `-${column}`;
  return column;
}
