import { ChevronLeft, ListFilter, Pencil, Plus, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router";
import { toast } from "sonner";

import { useCuratorHistory, useCurriculum, useGroup, useSend, useStaff, useStudents, useYears } from "@/api/hooks";
import { apiGet, apiSend } from "@/lib/api";
import type { Group, Staff } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { TextField } from "@/components/Field";
import { SectionTitle, SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { Cipher } from "@/components/world/Cipher";
import { CourseTab } from "@/components/world/CourseTab";
import { DemoMark } from "@/components/world/DemoMark";
import { SignalMargin } from "@/components/world/Signal";
import { Button, buttonVariants } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useQueryClient } from "@tanstack/react-query";
import { formatDate, todayIso } from "@/lib/format";
import { CONTROL_FORM, FORM, FUNDING, LEVEL, label } from "@/lib/labels";
import { signalsFor } from "@/lib/signals";

import { GroupDialog } from "./GroupDialog";

export function GroupPage() {
  const { id = "" } = useParams();
  const group = useGroup(id);
  const students = useStudents(new URLSearchParams({ group_id: id, size: "200" }));
  const curriculum = useCurriculum(id);
  const curators = useCuratorHistory(id);
  const [assigning, setAssigning] = useState(false);
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState(false);

  if (group.error) return <ErrorState error={group.error} onRetry={() => group.refetch()} />;
  const g = group.data;
  return (
    <div className="px-6 pt-4 pb-10">
      <Link to="/groups" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft className="size-4" aria-hidden /> Усі групи
      </Link>
      <div className="mt-4 pl-4"><CourseTab course={g?.course ?? null} raised /></div>
      <header className="rounded-md rounded-tl-none bg-card px-6 py-5 shadow-[0_8px_24px_-12px_oklch(0.2_0.03_165/0.3),0_1px_3px_oklch(0.2_0.03_165/0.1)]">
        {g ? (
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1"><GroupHeader g={g} count={students.data?.total} /></div>
            <Button variant="outline" className="h-8 shrink-0" onClick={() => setEditing(true)}><Pencil aria-hidden />Редагувати групу</Button>
          </div>
        ) : <Skeleton className="h-16 w-full" />}
      </header>

      <SectionTitle actions={<Button variant="outline" className="h-8" onClick={() => setAssigning(true)}><UserPlus aria-hidden />Призначити куратора</Button>}>
        Кураторство <DemoMark className="ml-2 align-middle" />
      </SectionTitle>
      <SimpleTable caption="Історія кураторства" rows={curators.data ?? []} rowKey={(c) => c.id} empty="Куратора ще не призначено."
        columns={[
          { header: "Куратор", cell: (c) => <span className="font-medium">{c.staff.full_name}</span> },
          { header: "Посада", cell: (c) => c.staff.position ?? "—" },
          { header: "З", className: "tabular", cell: (c) => formatDate(c.starts_on) },
          { header: "По", className: "tabular", cell: (c) => (c.ends_on ? formatDate(c.ends_on) : <span className="font-medium">дотепер</span>) },
        ]} />

      <SectionTitle actions={
        <Link to={`/students?group_id=${id}`} className={buttonVariants({ variant: "outline", className: "h-8" })}>
          <ListFilter aria-hidden />Відкрити в реєстрі
        </Link>
      }>
        Студенти
      </SectionTitle>
      <SimpleTable caption="Студенти групи" rows={students.data?.items ?? []} rowKey={(s) => s.id} empty="У групі немає студентів."
        columns={[
          { header: "", className: "w-12 pr-0", cell: (s) => <SignalMargin signals={signalsFor(s)} /> },
          { header: "ПІБ", cell: (s) => <Link to={`/students/${s.id}`} className="font-medium hover:underline">{s.full_name}</Link> },
          { header: "Фінансування", cell: (s) => label(FUNDING, s.funding) },
          { header: "№ залікової", cell: (s) => (s.record_book_no ? <Cipher>{s.record_book_no}</Cipher> : "—") },
        ]} />

      <SectionTitle actions={<Button variant="outline" className="h-8" onClick={() => setAdding(true)}><Plus aria-hidden />Додати дисципліну</Button>}>
        Навчальний план
      </SectionTitle>
      <SimpleTable caption="Навчальний план" rows={curriculum.data ?? []} rowKey={(d) => d.id} empty="Дисциплін ще не додано."
        columns={[
          { header: "Семестр", className: "whitespace-nowrap", cell: (d) => `${d.academic_year}, ${d.semester}-й` },
          { header: "Дисципліна", cell: (d) => <span className="font-medium">{d.discipline}</span> },
          { header: "Контроль", cell: (d) => label(CONTROL_FORM, d.control_form) },
          { header: "Кредити ЄКТС", className: "tabular", cell: (d) => d.credits_ects ?? "—" },
        ]} />

      <CuratorDialog open={assigning} onOpenChange={setAssigning} groupId={id} />
      {g && <GroupDialog open={editing} onOpenChange={setEditing} group={g} />}
      <DisciplineDialog open={adding} onOpenChange={setAdding} groupId={id} />
    </div>
  );
}

function GroupHeader({ g, count }: { g: Group; count?: number }) {
  return (
    <>
      <h1 className="text-[1.5rem] leading-tight font-semibold tracking-tight"><Cipher className="text-[1.375rem]">{g.code}</Cipher></h1>
      <p className="mt-1.5 text-sm text-muted-foreground">
        {g.specialty.code} {g.specialty.name}{g.program ? ` · ОП «${g.program.name}»` : ""} · {label(LEVEL, g.level)}, {label(FORM, g.form).toLowerCase()} форма
      </p>
      <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-2 border-t border-border pt-4 text-sm">
        {([
          ["Студентів", count ?? "…"],
          ["Рік вступу", g.is_shortened ? `${g.admission_year}, на ${g.entry_course}-й курс` : g.admission_year],
          ["Термін", g.study_start ? `${formatDate(g.study_start)} – ${formatDate(g.study_end)}` : "—"],
          ["Куратор", g.curator?.full_name ?? "не призначено"],
          ["Підрозділ", g.org_unit.name],
        ] as const).map(([k, v]) => (
          <div key={k} className="flex items-baseline gap-2"><dt className="text-muted-foreground">{k}</dt><dd className="font-medium tabular">{v}</dd></div>
        ))}
      </dl>
    </>
  );
}

function CuratorDialog({ open, onOpenChange, groupId }: { open: boolean; onOpenChange: (o: boolean) => void; groupId: string }) {
  const staff = useStaff("");
  const [staffId, setStaffId] = useState("");
  const [startsOn, setStartsOn] = useState(todayIso());
  const [newStaff, setNewStaff] = useState({ last_name: "", first_name: "", patronymic: "", position: "" });
  const [creating, setCreating] = useState(false);
  const qc = useQueryClient();
  const assign = useSend<object, unknown>("POST", `/api/groups/${groupId}/curator`, [["group", groupId], ["groups"], ["students"]]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    let id = staffId;
    try {
      if (creating) {
        const created = await apiSend<Staff>("POST", "/api/staff", {
          last_name: newStaff.last_name.trim(), first_name: newStaff.first_name.trim(),
          patronymic: newStaff.patronymic.trim() || null, position: newStaff.position.trim() || null,
        });
        id = created.id;
        qc.invalidateQueries({ queryKey: ["staff"] });
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Не вдалося створити співробітника");
      return;
    }
    assign.mutate({ staff_id: id, starts_on: startsOn }, {
      onSuccess: () => { toast.success("Куратора призначено"); onOpenChange(false); },
    });
  };
  const valid = creating ? newStaff.last_name.trim() && newStaff.first_name.trim() : staffId;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form className="contents" onSubmit={submit}>
          <DialogHeader>
            <DialogTitle>Призначити куратора</DialogTitle>
            <DialogDescription>Попереднє кураторство завершиться в день початку нового.</DialogDescription>
          </DialogHeader>
          {creating ? (
            <div className="grid grid-cols-2 gap-3">
              <TextField label="Прізвище" value={newStaff.last_name} onChange={(v) => setNewStaff({ ...newStaff, last_name: v })} required />
              <TextField label="Ім’я" value={newStaff.first_name} onChange={(v) => setNewStaff({ ...newStaff, first_name: v })} required />
              <TextField label="По батькові" value={newStaff.patronymic} onChange={(v) => setNewStaff({ ...newStaff, patronymic: v })} />
              <TextField label="Посада" value={newStaff.position} onChange={(v) => setNewStaff({ ...newStaff, position: v })} placeholder="доцент кафедри…" />
            </div>
          ) : (
            <FilterSelect label="Співробітник" allLabel={staff.data?.items.length ? "Оберіть зі списку" : "Список порожній"} value={staffId} onChange={setStaffId}
              options={(staff.data?.items ?? []).map((s) => ({ value: s.id, label: s.position ? `${s.full_name}, ${s.position}` : s.full_name }))} />
          )}
          <Button type="button" variant="link" className="h-auto justify-start p-0 text-sm" onClick={() => setCreating(!creating)}>
            {creating ? "Обрати з наявних співробітників" : "Немає у списку? Додати нового співробітника"}
          </Button>
          <TextField label="Початок кураторства" type="date" value={startsOn} onChange={setStartsOn} required />
          {assign.error && <p role="alert" className="text-sm text-destructive">{assign.error.message}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Скасувати</Button>
            <Button type="submit" disabled={!valid || assign.isPending}>Призначити</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function DisciplineDialog({ open, onOpenChange, groupId }: { open: boolean; onOpenChange: (o: boolean) => void; groupId: string }) {
  const years = useYears();
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [yearId, setYearId] = useState("");
  const [semester, setSemester] = useState("1");
  const [control, setControl] = useState("exam");
  const [credits, setCredits] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const year = yearId || years.data?.find((y) => y.is_current)?.id || "";

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPending(true);
    setError("");
    try {
      const sems = await apiGet<{ id: string; number: number }[]>("/api/semesters", new URLSearchParams({ academic_year_id: year }));
      const sem = sems.find((s) => s.number === Number(semester))
        ?? await apiSend<{ id: string }>("POST", "/api/semesters", { academic_year_id: year, number: Number(semester) });
      const disc = await apiSend<{ id: string }>("POST", "/api/disciplines", { name: name.trim() });
      await apiSend("POST", "/api/group-disciplines", {
        group_id: groupId, discipline_id: disc.id, semester_id: sem.id, control_form: control, credits_ects: credits || null,
      });
      qc.invalidateQueries({ queryKey: ["group", groupId] });
      toast.success(`Дисципліну «${name}» додано до плану`);
      setName("");
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося зберегти");
    } finally {
      setPending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form className="contents" onSubmit={submit}>
          <DialogHeader>
            <DialogTitle>Дисципліна навчального плану</DialogTitle>
            <DialogDescription>Після додавання студентам групи можна вносити оцінки з цієї дисципліни.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <TextField label="Назва дисципліни" value={name} onChange={setName} required />
            <div className="grid grid-cols-2 gap-3">
              <FilterSelect label="Навчальний рік" allLabel={years.data?.length ? "Оберіть рік" : "Немає років"} value={year} onChange={setYearId}
                options={(years.data ?? []).map((y) => ({ value: y.id, label: y.label }))} />
              <FilterSelect label="Семестр" allLabel="—" value={semester} onChange={(v) => setSemester(v || "1")}
                options={[{ value: "1", label: "1-й" }, { value: "2", label: "2-й" }]} />
              <FilterSelect label="Форма контролю" allLabel="—" value={control} onChange={(v) => setControl(v || "exam")}
                options={Object.entries(CONTROL_FORM).map(([value, l]) => ({ value, label: l }))} />
              <TextField label="Кредити ЄКТС" value={credits} onChange={setCredits} inputMode="decimal" />
            </div>
          </div>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Скасувати</Button>
            <Button type="submit" disabled={!name.trim() || !year || pending}>{pending ? "Збереження…" : "Додати"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
