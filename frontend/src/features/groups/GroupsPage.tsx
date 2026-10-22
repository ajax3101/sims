import { Plus } from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router";

import { useDictionaries, useGroups } from "@/api/hooks";
import type { Group } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { PageHeader } from "@/components/PageHeader";
import { SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { Cipher } from "@/components/world/Cipher";
import { CourseChips } from "@/components/world/CourseChips";
import { CourseTab } from "@/components/world/CourseTab";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { courseClass } from "@/lib/course";
import { formatDate } from "@/lib/format";
import { FORM, LEVEL, label } from "@/lib/labels";
import { plural } from "@/lib/plural";
import { cn } from "@/lib/utils";

import { GroupDialog } from "./GroupDialog";

const KEYS = ["specialty_id", "course", "level", "form", "q"] as const;

export function GroupsPage() {
  const [params, setParams] = useSearchParams();
  const dict = useDictionaries();
  const api = new URLSearchParams({ size: "200" });
  for (const k of KEYS) if (params.get(k)) api.set(k, params.get(k)!);
  const groups = useGroups(api);
  const set = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next, { replace: true });
  };
  const total = groups.data?.total ?? 0;
  const [creating, setCreating] = useState(false);
  return (
    <>
      <PageHeader title="Групи" meta={groups.data ? `${total} ${plural(total, ["група", "групи", "груп"])}` : "Завантаження…"}
        actions={<Button className="h-8" onClick={() => setCreating(true)}><Plus aria-hidden />Нова група</Button>} />
      <GroupDialog open={creating} onOpenChange={setCreating} />
      <section aria-label="Фільтри" className="grid grid-cols-[repeat(auto-fill,minmax(11rem,1fr))] items-end gap-3 border-y border-border bg-strip px-6 py-3 xl:grid-cols-[9rem_minmax(14rem,1.4fr)_auto_minmax(9rem,1fr)_minmax(9rem,1fr)]">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Шифр групи</span>
          <Input value={params.get("q") ?? ""} onChange={(e) => set("q", e.target.value)} placeholder="напр. G19" className="h-8 bg-card" />
        </label>
        <FilterSelect label="Спеціальність" value={params.get("specialty_id") ?? ""} onChange={(v) => set("specialty_id", v)} className="col-span-2 xl:col-span-1"
          options={(dict.data?.specialties ?? []).map((s) => ({ value: s.id, label: `${s.code} · ${s.name}` }))} />
        <fieldset className="col-span-2 flex min-w-0 flex-col gap-1 max-md:col-span-1 xl:col-span-1">
          <legend className="mb-1 text-xs font-medium text-muted-foreground">Курс</legend>
          <CourseChips value={params.get("course") ?? ""} onChange={(v) => set("course", v)} />
        </fieldset>
        <FilterSelect label="Рівень" value={params.get("level") ?? ""} onChange={(v) => set("level", v)}
          options={Object.entries(LEVEL).map(([value, l]) => ({ value, label: l }))} />
        <FilterSelect label="Форма" value={params.get("form") ?? ""} onChange={(v) => set("form", v)}
          options={Object.entries(FORM).map(([value, l]) => ({ value, label: l }))} />
      </section>
      <div className="px-6 py-5">
        {groups.error ? <ErrorState error={groups.error} onRetry={() => groups.refetch()} />
          : !groups.data ? <Skeleton className="h-64 w-full" />
          : <CourseSummary groups={groups.data.items} active={params.get("course") ?? ""} onPick={(v) => set("course", v)} />}
        {groups.data && (
          <SimpleTable<Group>
            caption="Групи"
            rows={groups.data.items}
            rowKey={(g) => g.id}
            empty="Груп за цими умовами немає."
            columns={[
              { header: "Шифр", className: "whitespace-nowrap", cell: (g) => <Link to={`/groups/${g.id}`} className="font-medium hover:underline"><Cipher>{g.code}</Cipher></Link> },
              { header: "Курс", cell: (g) => <CourseTab course={g.course} /> },
              {
                header: "Спеціальність / освітня програма",
                cell: (g) => {
                  const own = g.program && g.program.name.toLocaleLowerCase("uk") !== g.specialty.name.toLocaleLowerCase("uk");
                  const full = `${g.specialty.code} ${g.specialty.name}${own ? ` — ОП «${g.program!.name}»` : ""}`;
                  return (
                    <span className="block max-w-[21rem] truncate" title={full}>
                      <span className="font-medium">{g.specialty.code}</span> <span className="text-muted-foreground">{g.specialty.name}</span>
                      {own && <> · <span>ОП «{g.program!.name}»</span></>}
                      {!g.program && <span className="text-muted-foreground"> · ОП не вказано</span>}
                    </span>
                  );
                },
              },
              { header: "Рівень / форма", className: "whitespace-nowrap", cell: (g) => `${label(LEVEL, g.level)}, ${label(FORM, g.form).toLowerCase()}` },
              { header: "Куратор", className: "min-w-[13rem] whitespace-nowrap", cell: (g) => g.curator?.full_name ?? <span className="text-muted-foreground">—</span> },
              { header: "Термін навчання", className: "tabular whitespace-nowrap", cell: (g) => (g.study_start ? `${formatDate(g.study_start)} – ${formatDate(g.study_end)}` : "—") },
            ]}
          />
        )}
      </div>
    </>
  );
}

/** How the file divides by course: one strip of index tabs, each as wide as its share of groups. */
function CourseSummary({ groups, active, onPick }: { groups: Group[]; active: string; onPick: (course: string) => void }) {
  if (!groups.length) return null;
  const counts = new Map<number | null, number>();
  for (const g of groups) counts.set(g.course, (counts.get(g.course) ?? 0) + 1);
  const entries = [...counts.entries()].toSorted((a, b) => (a[0] ?? 99) - (b[0] ?? 99));
  return (
    <div role="group" className="mb-4 flex h-7 gap-px overflow-hidden rounded-md" aria-label="Розподіл груп за курсами (натисніть, щоб відфільтрувати)">
      {entries.map(([course, n]) => {
        const value = course ? String(course) : "";
        const pressed = !!value && active === value;
        return (
          <button key={course ?? "none"} type="button" style={{ flexGrow: n }} aria-pressed={pressed} disabled={!course}
            onClick={() => onPick(pressed ? "" : value)}
            className={cn("flex min-w-12 items-center justify-center text-xs font-medium text-course-ink tabular transition-[filter] duration-150",
              "hover:brightness-95 disabled:cursor-default", courseClass(course), pressed && "ring-2 ring-foreground/40 ring-inset")}>
            {course ? `${course} курс` : "без курсу"} · {n}
          </button>
        );
      })}
    </div>
  );
}
