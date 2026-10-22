import { Plus, Search } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";

import { useStudents } from "@/api/hooks";
import type { StudentListItem } from "@/api/types";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState } from "@/components/States";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { plural } from "@/lib/plural";

import { FilterStrip } from "./FilterStrip";
import { Pager } from "./Pager";
import { StudentFormDialog } from "./StudentFormDialog";
import { StudentPeek } from "./StudentPeek";
import { StudentsTable } from "./StudentsTable";
import { useStudentQuery } from "./useStudentQuery";

export function StudentsPage() {
  const state = useStudentQuery();
  const students = useStudents(state.apiParams);
  const navigate = useNavigate();
  const [peek, setPeek] = useState<StudentListItem | null>(null);
  const [creating, setCreating] = useState(false);
  const closePeek = useCallback(() => setPeek(null), []);
  const total = students.data?.total ?? 0;

  return (
    <>
      <PageHeader
        title="Студенти"
        meta={students.data ? `${total} ${plural(total, ["запис", "записи", "записів"])}` : "Завантаження…"}
        actions={
          <>
            <SearchBox value={state.query.filters.q ?? ""} onChange={(v) => state.setFilter("q", v)} />
            <Button onClick={() => setCreating(true)} className="h-8">
              <Plus aria-hidden />
              Додати студента
            </Button>
          </>
        }
      />
      <FilterStrip query={state.query} setFilter={state.setFilter} reset={state.reset} activeFilters={state.activeFilters} />

      {students.error ? (
        <ErrorState error={students.error} onRetry={() => students.refetch()} />
      ) : students.data && students.data.items.length === 0 ? (
        <EmptyState
          title="Нікого не знайдено"
          hint={state.activeFilters || state.query.filters.q
            ? "Жоден студент не відповідає цим фільтрам. Послабте умови або скиньте фільтри."
            : "Реєстр порожній. Імпортуйте списки груп у розділі «Імпорт» або додайте студента вручну."}
          action={state.activeFilters || state.query.filters.q ? <Button variant="outline" onClick={state.reset}>Скинути фільтри</Button> : undefined}
        />
      ) : (
        <>
          <StudentsTable
            rows={students.data?.items ?? []}
            sort={state.query.sort}
            onSort={state.setSort}
            onOpen={setPeek}
            onActivate={(row) => (peek?.id === row.id ? navigate(`/students/${row.id}`) : setPeek(row))}
            loading={students.isFetching}
            selectedId={peek?.id}
          />
          <Pager page={state.query.page} size={state.query.size} total={total} onPage={state.setPage} onSize={state.setSize} />
        </>
      )}

      <StudentPeek student={peek} onClose={closePeek} />
      <StudentFormDialog open={creating} onOpenChange={setCreating} />
    </>
  );
}

/** Typing updates the URL after a short pause; the URL stays the source of truth (reset clears the box too). */
function SearchBox({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [text, setText] = useState(value);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;
  useEffect(() => setText(value), [value]);
  useEffect(() => {
    if (text === value) return;
    const t = setTimeout(() => onChangeRef.current(text), 300);
    return () => clearTimeout(t);
  }, [text, value]);
  return (
    <div className="relative max-sm:w-full">
      <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
      <Input
        type="search"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="ПІБ, № залікової або ІПН"
        aria-label="Пошук студента"
        className="h-8 w-72 bg-card pl-8 max-sm:w-full"
      />
    </div>
  );
}
