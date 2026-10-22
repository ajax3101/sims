import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";

import { type FilterKey, type StudentQuery, nextSort, parseStudentQuery, toApiParams, withFilter } from "@/lib/studentQuery";

/** The register's state lives in the URL, so a filtered view can be bookmarked, shared and restored with Back. */
export function useStudentQuery() {
  const [params, setParams] = useSearchParams();
  const query = useMemo(() => parseStudentQuery(params), [params]);

  const commit = useCallback(
    (next: StudentQuery) => {
      const url = toApiParams(next);
      if (next.page === 1) url.delete("page");
      if (next.size === 50) url.delete("size");
      if (next.sort === "name") url.delete("sort");
      setParams(url, { replace: true });
    },
    [setParams],
  );

  return {
    query,
    apiParams: useMemo(() => toApiParams(query), [query]),
    setFilter: (key: FilterKey, value: string) => commit(withFilter(query, key, value)),
    setSort: (column: string) => commit({ ...query, page: 1, sort: nextSort(query.sort, column) }),
    setPage: (page: number) => commit({ ...query, page }),
    setSize: (size: number) => commit({ ...query, page: 1, size }),
    reset: () => commit({ page: 1, size: query.size, sort: query.sort, filters: {} }),
    activeFilters: Object.keys(query.filters).filter((k) => k !== "q").length,
  };
}
