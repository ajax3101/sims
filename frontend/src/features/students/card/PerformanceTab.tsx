import { CalendarClock, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useCurriculum, usePerformance, useSend } from "@/api/hooks";
import type { Performance, Student } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { TextField } from "@/components/Field";
import { SectionTitle, SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { DemoMark } from "@/components/world/DemoMark";
import { SignalClip } from "@/components/world/Signal";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate, todayIso } from "@/lib/format";
import { markFresh } from "@/lib/fresh";
import { CONTROL_FORM, DEBT_STATUS, GRADE_KIND, NATIONAL, label } from "@/lib/labels";

const UNRESOLVED = new Set(["open", "retake_scheduled"]);

export function usePerformanceSignal(studentId: string): boolean {
  const perf = usePerformance(studentId);
  return !!perf.data?.debts.some((d) => UNRESOLVED.has(d.status));
}

type Debt = Performance["debts"][number];

export function PerformanceTab({ student }: { student: Student }) {
  const perf = usePerformance(student.id);
  const [grading, setGrading] = useState(false);
  const [debt, setDebt] = useState<Debt | null>(null);

  if (perf.error) return <ErrorState error={perf.error} onRetry={() => perf.refetch()} />;
  if (!perf.data) return <Skeleton className="h-40 w-full" />;
  const { semesters, debts } = perf.data;
  const open = debts.filter((d) => UNRESOLVED.has(d.status));

  return (
    <div>
      <SectionTitle actions={
        <Button variant="outline" className="h-8" onClick={() => setGrading(true)} disabled={!student.group}>
          <Plus aria-hidden />Додати оцінку
        </Button>
      }>
        Академічні заборгованості {open.length > 0 && <span className="text-destructive tabular">· {open.length}</span>}
        <DemoMark className="ml-2 align-middle" />
      </SectionTitle>
      <SimpleTable
        caption="Академічні заборгованості"
        rows={debts}
        rowKey={(d) => d.id}
        empty="Заборгованостей немає."
        columns={[
          { header: "", className: "w-8 pr-0", cell: (d) => (UNRESOLVED.has(d.status) ? <SignalClip kind="academic" /> : null) },
          { header: "Дисципліна", cell: (d) => <span className="font-medium">{d.discipline}</span> },
          { header: "Семестр", cell: (d) => `${d.academic_year}, ${d.semester}-й` },
          { header: "Статус", cell: (d) => label(DEBT_STATUS, d.status) },
          { header: "Відкрито", className: "tabular", cell: (d) => formatDate(d.opened_on) },
          { header: "Перескласти до", className: "tabular", cell: (d) => formatDate(d.retake_deadline) },
          { header: "Закрито", className: "tabular", cell: (d) => formatDate(d.closed_on) },
          {
            header: "Дії", className: "text-right",
            cell: (d) => UNRESOLVED.has(d.status) ? (
              <Button size="sm" variant="ghost" onClick={() => setDebt(d)}><CalendarClock aria-hidden />Перескладання</Button>
            ) : null,
          },
        ]}
      />

      {semesters.length === 0 ? (
        <>
          <SectionTitle>Успішність</SectionTitle>
          <p className="rounded-md border border-dashed border-border bg-card px-5 py-6 text-sm text-muted-foreground">
            Оцінок ще немає. Дисципліни з’являються тут, коли їх додано до навчального плану групи
            {student.group ? <> на сторінці групи</> : null}; оцінку вносять кнопкою «Додати оцінку».
          </p>
        </>
      ) : semesters.map((sem) => (
        <section key={`${sem.academic_year}-${sem.semester}`} className="mt-8">
          <SectionTitle>{sem.academic_year} н. р., {sem.semester}-й семестр</SectionTitle>
          <SimpleTable
            rows={sem.disciplines}
            rowKey={(d) => d.group_discipline_id}
            empty="Немає дисциплін."
            columns={[
              { header: "", className: "w-8 pr-0", cell: (d) => (d.has_debt ? <SignalClip kind="academic" /> : null) },
              { header: "Дисципліна", cell: (d) => <span className="font-medium">{d.discipline}</span> },
              { header: "Контроль", cell: (d) => label(CONTROL_FORM, d.control_form) },
              { header: "Кредити", className: "tabular", cell: (d) => d.credits_ects ?? "—" },
              { header: "Бал", className: "tabular font-medium", cell: (d) => d.final?.score ?? "—" },
              { header: "ECTS", cell: (d) => d.final?.ects ?? "—" },
              { header: "Оцінка", cell: (d) => (d.final ? label(NATIONAL, d.final.national) : "—") },
              {
                header: "Спроби", className: "text-muted-foreground",
                cell: (d) => d.grades.filter((x) => x.kind !== "current")
                  .map((x) => `${label(GRADE_KIND, x.kind).toLowerCase()} ${x.score ?? "—"} (${formatDate(x.graded_on)})`).join("; ") || "—",
              },
            ]}
          />
        </section>
      ))}

      {student.group && <GradeDialog open={grading} onOpenChange={setGrading} studentId={student.id} groupId={student.group.id} />}
      <DebtDialog debt={debt} onClose={() => setDebt(null)} studentId={student.id} />
    </div>
  );
}

function GradeDialog({ open, onOpenChange, studentId, groupId }: { open: boolean; onOpenChange: (o: boolean) => void; studentId: string; groupId: string }) {
  const curriculum = useCurriculum(groupId);
  const [gd, setGd] = useState("");
  const [kind, setKind] = useState("final");
  const [score, setScore] = useState("");
  const [date, setDate] = useState(todayIso());
  const send = useSend<object, { national: string | null }>("POST", "/api/grades", [["student", studentId], ["students"]]);
  const scoreNum = Number(score);
  const valid = gd && score !== "" && Number.isInteger(scoreNum) && scoreNum >= 0 && scoreNum <= 100;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form className="contents" onSubmit={(e) => {
          e.preventDefault();
          if (!valid) return;
          send.mutate({ student_id: studentId, group_discipline_id: gd, kind, score: scoreNum, graded_on: date }, {
            onSuccess: (g) => {
              markFresh(studentId);
              toast.success(`Оцінку внесено: ${scoreNum} (${label(NATIONAL, g.national)})`);
              onOpenChange(false);
              setScore("");
            },
          });
        }}>
          <DialogHeader>
            <DialogTitle>Додати оцінку</DialogTitle>
            <DialogDescription>Підсумкова нижче 60 відкриває заборгованість; успішне перескладання її закриває.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <FilterSelect label="Дисципліна навчального плану" allLabel="Оберіть дисципліну" value={gd} onChange={setGd}
              options={(curriculum.data ?? []).map((d) => ({ value: d.id, label: `${d.discipline} · ${d.academic_year}, ${d.semester} сем.` }))} />
            {curriculum.data?.length === 0 && (
              <p className="text-xs text-muted-foreground">У навчальному плані групи ще немає дисциплін. Додайте їх на сторінці групи.</p>
            )}
            <div className="grid grid-cols-2 gap-3">
              <FilterSelect label="Вид" allLabel="—" value={kind} onChange={(v) => setKind(v || "final")}
                options={Object.entries(GRADE_KIND).map(([value, l]) => ({ value, label: l }))} />
              <TextField label="Бал (0–100)" value={score} onChange={setScore} inputMode="numeric"
                error={score !== "" && !valid && gd ? "Ціле число від 0 до 100" : undefined} />
            </div>
            <TextField label="Дата" type="date" value={date} onChange={setDate} />
          </div>
          {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Скасувати</Button>
            <Button type="submit" disabled={!valid || send.isPending}>{send.isPending ? "Збереження…" : "Внести оцінку"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function DebtDialog({ debt, onClose, studentId }: { debt: Debt | null; onClose: () => void; studentId: string }) {
  const [deadline, setDeadline] = useState("");
  const [note, setNote] = useState("");
  const send = useSend<object, unknown>("PATCH", () => `/api/academic-debts/${debt?.id}`, [["student", studentId], ["students"]]);
  return (
    <Dialog open={!!debt} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-md">
        {debt && (
          <form className="contents" onSubmit={(e) => {
            e.preventDefault();
            send.mutate({ status: "retake_scheduled", retake_deadline: deadline || null, note: note || null }, {
              onSuccess: () => { markFresh(studentId); toast.success("Перескладання призначено"); onClose(); },
            });
          }}>
            <DialogHeader>
              <DialogTitle>Призначити перескладання</DialogTitle>
              <DialogDescription>{debt.discipline}, {debt.academic_year}, {debt.semester}-й семестр</DialogDescription>
            </DialogHeader>
            <div className="grid gap-3">
              <TextField label="Перескласти до" type="date" value={deadline} onChange={setDeadline} required />
              <TextField label="Примітка" value={note} onChange={setNote} placeholder="аудиторія, комісія…" />
            </div>
            {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={onClose}>Скасувати</Button>
              <Button type="submit" disabled={!deadline || send.isPending}>Призначити</Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
