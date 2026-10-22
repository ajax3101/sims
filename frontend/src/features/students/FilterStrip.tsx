import { ChevronDown, RotateCcw, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

import { useAllGroups, useDictionaries, useStaff } from "@/api/hooks";
import { FilterSelect } from "@/components/FilterSelect";
import { CourseChips } from "@/components/world/CourseChips";
import { Button } from "@/components/ui/button";
import { FORM, FUNDING, LEVEL, STATUS } from "@/lib/labels";
import type { FilterKey, StudentQuery } from "@/lib/studentQuery";
import { cn } from "@/lib/utils";

const toOptions = (map: Record<string, string>) => Object.entries(map).map(([value, label]) => ({ value, label }));

export function FilterStrip({
  query, setFilter, reset, activeFilters,
}: {
  query: StudentQuery;
  setFilter: (key: FilterKey, value: string) => void;
  reset: () => void;
  activeFilters: number;
}) {
  const dict = useDictionaries();
  const groups = useAllGroups();
  const staff = useStaff("");
  const f = query.filters;
  const [open, setOpen] = useState(false);

  const specialties = (dict.data?.specialties ?? [])
    .toSorted((a, b) => b.classifier.localeCompare(a.classifier) || a.code.localeCompare(b.code, "uk", { numeric: true }))
    .map((s) => ({ value: s.id, label: `${s.code} · ${s.name}` }));
  const groupOptions = (groups.data?.items ?? [])
    .filter((g) => !f.specialty_id || g.specialty.id === f.specialty_id)
    .filter((g) => !f.course || String(g.course) === f.course)
    .map((g) => ({ value: g.id, label: g.code }));

  return (
    <section aria-label="Фільтри" className="border-y border-border bg-strip px-6 py-3">
      <Button variant="outline" className="h-8 w-full justify-between bg-card md:hidden" aria-expanded={open}
        aria-controls="student-filters" onClick={() => setOpen(!open)}>
        <span className="inline-flex items-center gap-2"><SlidersHorizontal aria-hidden />Фільтри{activeFilters ? ` (${activeFilters})` : ""}</span>
        <ChevronDown className={cn("transition-transform duration-150", open && "rotate-180")} aria-hidden />
      </Button>
      <div id="student-filters" className={cn(
        "grid grid-cols-[repeat(auto-fill,minmax(10.5rem,1fr))] items-end gap-x-3 gap-y-2.5 max-md:grid-cols-1",
        open ? "max-md:mt-3" : "max-md:hidden",
      )}>
        <FilterSelect label="Спеціальність" value={f.specialty_id} options={specialties}
          onChange={(v) => setFilter("specialty_id", v)} className="col-span-2 max-md:col-span-1" />
        <fieldset className="col-span-2 flex min-w-0 flex-col gap-1 max-md:col-span-1">
          <legend className="mb-1 text-xs font-medium text-muted-foreground">Курс</legend>
          <CourseChips value={f.course ?? ""} onChange={(v) => setFilter("course", v)} />
        </fieldset>
        <FilterSelect label="Група" value={f.group_id} options={groupOptions} onChange={(v) => setFilter("group_id", v)} />
        <FilterSelect label="Куратор" value={f.curator_id}
          options={(staff.data?.items ?? []).map((s) => ({ value: s.id, label: s.full_name }))}
          onChange={(v) => setFilter("curator_id", v)} />
        <FilterSelect label="Рівень" value={f.level} options={toOptions(LEVEL)} onChange={(v) => setFilter("level", v)} />
        <FilterSelect label="Форма" value={f.form} options={toOptions(FORM)} onChange={(v) => setFilter("form", v)} />
        <FilterSelect label="Фінансування" value={f.funding} options={toOptions(FUNDING)} onChange={(v) => setFilter("funding", v)} />
        <FilterSelect label="Статус" value={f.status} options={toOptions(STATUS)} onChange={(v) => setFilter("status", v)} />
        <div className="col-span-2 flex flex-wrap items-end gap-2 max-md:col-span-1">
          <DebtToggle label="Академборг" signal="bg-signal-academic" pressed={f.has_academic_debt === "true"}
            onClick={() => setFilter("has_academic_debt", f.has_academic_debt === "true" ? "" : "true")} />
          <DebtToggle label="Фінборг" signal="bg-signal-tuition" pressed={f.has_financial_debt === "true"}
            onClick={() => setFilter("has_financial_debt", f.has_financial_debt === "true" ? "" : "true")} />
          <Button variant="ghost" size="sm" onClick={reset} disabled={!activeFilters} className="ml-auto h-8">
            <RotateCcw aria-hidden />
            Скинути{activeFilters ? ` (${activeFilters})` : ""}
          </Button>
        </div>
      </div>
    </section>
  );
}

function DebtToggle({ label, signal, pressed, onClick }: { label: string; signal: string; pressed: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={cn(
        "inline-flex h-8 items-center gap-2 rounded-md border px-3 text-sm transition-colors duration-150",
        pressed ? "border-foreground/30 bg-card font-medium text-foreground" : "border-input bg-card/60 text-muted-foreground hover:bg-card",
      )}
    >
      <span aria-hidden className={cn("h-3.5 w-2 rounded-[1px]", signal, !pressed && "opacity-55")} />
      {label}
    </button>
  );
}
