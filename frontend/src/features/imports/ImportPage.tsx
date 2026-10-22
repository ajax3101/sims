import { FileUp, X } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { useImport } from "@/api/hooks";
import type { ImportReport, Issue } from "@/api/types";
import { PageHeader } from "@/components/PageHeader";
import { SimpleTable } from "@/components/SimpleTable";
import { SignalClip } from "@/components/world/Signal";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ACCEPT = [".docx", ".xlsx"];
const ISSUE_LABEL: Record<string, string> = {
  invalid_name: "Некоректне ПІБ", invalid_row: "Некоректні дані рядка", duplicate_in_file: "Повтор у файлі",
  funding_missing: "Не вказано фінансування", funding_unknown_code: "Невідомий код фінансування",
  group_code_repaired: "Шифр групи виправлено", program_missing: "Порожня освітня програма",
  program_fuzzy_matched: "ОП зіставлено з наявною", program_name_corrected: "Назву ОП виправлено",
  specialty_created: "Нова спеціальність", level_mismatch: "Рівень не збігається з шифром",
  header_missing_group: "У шапці немає групи", header_missing_institute: "У шапці немає підрозділу",
  invalid_group_code: "Нерозпізнаний шифр групи", unknown_group: "Групи немає в системі", missing_columns: "Немає потрібних колонок",
  row_missing_group: "У рядку не вказано групу", import_failed: "Імпорт файлу не вдався", name_extra_parts: "Зайві частини в ПІБ",
};

function where(loc: Issue["location"]): string {
  const parts = [];
  if (loc.table !== undefined) parts.push(`таблиця ${Number(loc.table) + 1}`);
  if (loc.row !== undefined) parts.push(`рядок ${loc.table !== undefined ? Number(loc.row) + 1 : loc.row}`);
  return parts.join(", ") || "—";
}

export function ImportPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const upload = useImport();
  const add = (list: FileList | null) => {
    const picked = [...(list ?? [])].filter((f) => ACCEPT.some((ext) => f.name.toLowerCase().endsWith(ext)));
    setFiles((prev) => [...prev, ...picked.filter((f) => !prev.some((p) => p.name === f.name && p.size === f.size))]);
  };

  return (
    <>
      <PageHeader title="Імпорт списків" meta="Word-списки груп (шапка + таблиця № / ПІБ / Б–К) і реєстри Excel із колонками ПІБ та Група" />
      <div className="grid gap-6 px-6 pb-10">
        <label
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); add(e.dataTransfer.files); }}
          className={cn(
            "flex cursor-pointer flex-col items-center gap-2 rounded-md border-2 border-dashed px-6 py-10 text-center transition-colors duration-150",
            dragging ? "border-primary bg-accent" : "border-input bg-card hover:bg-accent/50",
          )}
        >
          <FileUp className="size-6 text-muted-foreground" aria-hidden />
          <span className="font-medium">Перетягніть файли сюди або оберіть на диску</span>
          <span className="text-sm text-muted-foreground">.docx та .xlsx, кілька файлів одразу. Повторний імпорт не створює дублікатів.</span>
          <input type="file" multiple accept={ACCEPT.join(",")} className="sr-only" onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
        </label>

        {files.length > 0 && (
          <div className="rounded-md border border-border bg-card">
            <ul className="divide-y divide-border">
              {files.map((f) => (
                <li key={f.name + f.size} className="flex items-center justify-between gap-3 px-4 py-2 text-sm">
                  <span className="truncate">{f.name}</span>
                  <span className="flex items-center gap-3 text-muted-foreground tabular">
                    {(f.size / 1024).toFixed(0)} КБ
                    <Button variant="ghost" size="icon-sm" aria-label={`Прибрати ${f.name}`} onClick={() => setFiles(files.filter((x) => x !== f))}><X /></Button>
                  </span>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
              <Button variant="ghost" onClick={() => setFiles([])} disabled={upload.isPending}>Очистити</Button>
              <Button onClick={() => upload.mutate(files, { onSuccess: () => setFiles([]) })} disabled={upload.isPending}>
                {upload.isPending ? "Імпорт…" : `Імпортувати ${files.length}`}
              </Button>
            </div>
          </div>
        )}

        {upload.error && <p role="alert" className="text-sm text-destructive">{upload.error.message}</p>}
        {upload.data && (
          <section aria-label="Результати імпорту" className="grid gap-6">
            <Summary reports={upload.data} />
            {upload.data.map((r) => <FileReport key={r.batch_id ?? r.source_filename} report={r} />)}
          </section>
        )}
      </div>
    </>
  );
}

function Summary({ reports }: { reports: ImportReport[] }) {
  const sum = (k: "students_created" | "students_updated" | "duplicates" | "errors" | "warnings") => reports.reduce((a, r) => a + r[k], 0);
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-md bg-rail px-5 py-4 text-rail-foreground">
      <div className="flex flex-wrap gap-x-8 gap-y-1 text-sm">
        <span>Файлів: <b className="tabular">{reports.length}</b></span>
        <span>Нових студентів: <b className="tabular">{sum("students_created")}</b></span>
        <span>Оновлено: <b className="tabular">{sum("students_updated")}</b></span>
        <span>Дублікатів: <b className="tabular">{sum("duplicates")}</b></span>
        <span>Помилок: <b className="tabular">{sum("errors")}</b></span>
        <span>Попереджень: <b className="tabular">{sum("warnings")}</b></span>
      </div>
      <Link to="/students?sort=-created_at" className="text-sm font-medium underline">Переглянути в реєстрі</Link>
    </div>
  );
}

function FileReport({ report: r }: { report: ImportReport }) {
  const [only, setOnly] = useState<"all" | "error" | "warning">(r.errors ? "error" : "all");
  const issues = r.issues.filter((i) => only === "all" || i.severity === only);
  return (
    <article className="rounded-md border border-border bg-card">
      <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border px-5 py-3">
        <h2 className="font-semibold">{r.source_filename}</h2>
        <p className="text-sm text-muted-foreground tabular">
          створено {r.students_created} · оновлено {r.students_updated} · дублікатів {r.duplicates} · груп нових {r.groups_created}, наявних {r.groups_matched}
          {r.status !== "done" && <b className="ml-2 text-destructive">імпорт не виконано</b>}
        </p>
      </header>
      {r.issues.length > 0 ? (
        <div className="p-4">
          <div role="group" aria-label="Показати" className="mb-3 flex gap-1 text-sm">
            {([["all", `Усі ${r.issues.length}`], ["error", `Помилки ${r.errors}`], ["warning", `Попередження ${r.warnings}`]] as const).map(([v, l]) => (
              <Button key={v} size="sm" variant={only === v ? "secondary" : "ghost"} aria-pressed={only === v} onClick={() => setOnly(v)}>{l}</Button>
            ))}
          </div>
          <SimpleTable caption={`Проблеми у файлі ${r.source_filename}`} rows={issues} rowKey={(i) => `${i.code}-${JSON.stringify(i.location)}-${i.message}`} empty="Немає."
            columns={[
              { header: "", className: "w-8 pr-0", cell: (i) => <SignalClip kind={i.severity === "error" ? "academic" : "tuition"} /> },
              { header: "Що", cell: (i) => <span className="font-medium">{ISSUE_LABEL[i.code] ?? i.code}</span> },
              { header: "Де", className: "whitespace-nowrap tabular", cell: (i) => where(i.location) },
              { header: "Деталі", className: "text-muted-foreground", cell: (i) => i.message },
            ]} />
        </div>
      ) : <p className="px-5 py-4 text-sm text-muted-foreground">Без зауважень.</p>}
    </article>
  );
}
