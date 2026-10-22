import { FileDown } from "lucide-react";
import { useState } from "react";

import { useAllGroups, useDictionaries } from "@/api/hooks";
import { FilterSelect } from "@/components/FilterSelect";
import { PageHeader } from "@/components/PageHeader";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const REPORTS = {
  "academic-debts": {
    title: "Відомість академічних заборгованостей",
    text: "Відкриті борги та призначені перескладання: студент, група, курс, дисципліна, семестр, строки.",
  },
  "financial-debts": {
    title: "Фінансовий звіт заборгованостей з оплати",
    text: "Лише студенти з боргом на сьогодні: договір, нараховано до сплати, сплачено, борг; із підсумками.",
  },
} as const;
type Kind = keyof typeof REPORTS;
const FORMATS = ["xlsx", "docx", "pdf"] as const;

export function ReportsPage() {
  const dict = useDictionaries();
  const groups = useAllGroups();
  const [kind, setKind] = useState<Kind>("academic-debts");
  const [orgUnit, setOrgUnit] = useState("");
  const [department, setDepartment] = useState("");
  const [group, setGroup] = useState("");
  const [format, setFormat] = useState<(typeof FORMATS)[number]>("xlsx");

  const params = new URLSearchParams({ format });
  if (orgUnit) params.set("org_unit_id", orgUnit);
  if (kind === "academic-debts" && department) params.set("department_id", department);
  if (group) params.set("group_id", group);
  const units = dict.data?.org_units ?? [];

  return (
    <>
      <PageHeader title="Звіти" meta="Офіційні відомості для друку та підпису" />
      <div className="grid max-w-4xl gap-6 px-6 pb-10">
        <fieldset className="grid gap-2">
          <legend className="mb-2 text-sm font-semibold">Звіт</legend>
          {(Object.entries(REPORTS) as [Kind, (typeof REPORTS)[Kind]][]).map(([k, r]) => (
            <label key={k} className={cn(
              "flex cursor-pointer gap-3 rounded-md border bg-card px-4 py-3 transition-colors duration-150",
              kind === k ? "border-primary/60 bg-accent/50" : "border-border hover:bg-accent/30",
            )}>
              <input type="radio" name="report" value={k} checked={kind === k} onChange={() => setKind(k)} className="mt-1 accent-[var(--primary)]" />
              <span>
                <span className="block font-medium">{r.title}</span>
                <span className="block text-sm text-muted-foreground">{r.text}</span>
              </span>
            </label>
          ))}
          <p className="text-sm text-muted-foreground">Індивідуальну картку студента з випискою оцінок формують на сторінці студента.</p>
        </fieldset>

        <fieldset className="grid grid-cols-3 gap-3 max-sm:grid-cols-1">
          <legend className="mb-2 text-sm font-semibold">Охоплення</legend>
          <FilterSelect label="Факультет / інститут" allLabel="Усі підрозділи" value={orgUnit} onChange={setOrgUnit}
            options={units.filter((u) => u.kind !== "department").map((u) => ({ value: u.id, label: u.name }))} />
          {kind === "academic-debts" && (
            <FilterSelect label="Кафедра (дисципліни)" allLabel="Усі кафедри" value={department} onChange={setDepartment}
              options={units.filter((u) => u.kind === "department").map((u) => ({ value: u.id, label: u.name }))} />
          )}
          <FilterSelect label="Група" allLabel="Усі групи" value={group} onChange={setGroup}
            options={(groups.data?.items ?? []).map((g) => ({ value: g.id, label: g.code }))} />
        </fieldset>

        <div className="flex flex-wrap items-end justify-between gap-4 border-t border-border pt-5">
          <div role="radiogroup" aria-label="Формат" className="flex gap-1">
            {FORMATS.map((f) => (
              <button key={f} type="button" role="radio" aria-checked={format === f} onClick={() => setFormat(f)}
                className={cn("h-8 rounded-md border px-3 text-sm font-medium uppercase transition-colors duration-150",
                  format === f ? "border-transparent bg-rail text-rail-foreground" : "border-input bg-card text-muted-foreground hover:text-foreground")}>
                {f}
              </button>
            ))}
          </div>
          <a href={`/api/reports/${kind}?${params}`} className={buttonVariants({ className: "h-9" })}>
            <FileDown aria-hidden />Сформувати і завантажити
          </a>
        </div>
      </div>
    </>
  );
}
