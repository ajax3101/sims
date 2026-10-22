import { useNavigate } from "react-router";
import { toast } from "sonner";

import { useStudentMutation } from "@/api/hooks";
import type { Student } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

import { StudentFields, emptyStudent, fromStudent, toBody, useStudentForm } from "./StudentForm";

export function StudentFormDialog({
  open, onOpenChange, student, defaultGroupId,
}: { open: boolean; onOpenChange: (open: boolean) => void; student?: Student; defaultGroupId?: string }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        {open && <Body student={student} defaultGroupId={defaultGroupId} onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  );
}

function Body({ student, defaultGroupId, onDone }: { student?: Student; defaultGroupId?: string; onDone: () => void }) {
  const navigate = useNavigate();
  const form = useStudentForm(student ? fromStudent(student) : emptyStudent(defaultGroupId));
  const create = useStudentMutation<ReturnType<typeof toBody>>("POST", () => "/api/students");
  const patch = useStudentMutation<ReturnType<typeof toBody>>("PATCH", () => `/api/students/${student?.id}`);
  const mutation = student ? patch : create;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.valid) return;
    mutation.mutate(toBody(form.value, { withGroup: !student }), {
      onSuccess: (out) => {
        toast.success(student ? "Зміни збережено" : `Студента ${out.full_name} додано`);
        onDone();
        if (!student) navigate(`/students/${out.id}`);
      },
    });
  };

  return (
    <form onSubmit={submit} className="contents">
      <DialogHeader>
        <DialogTitle>{student ? "Редагувати дані студента" : "Новий студент"}</DialogTitle>
        <DialogDescription>
          {student ? "Групу змінюють через «Перевести», статус — через «Змінити статус»." : "Обов’язкові лише прізвище та ім’я."}
        </DialogDescription>
      </DialogHeader>
      <StudentFields value={form.value} onChange={form.setValue} showGroup={!student} errors={form.errors} />
      {mutation.error && <p role="alert" className="text-sm text-destructive">{mutation.error.message}</p>}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>Скасувати</Button>
        <Button type="submit" disabled={!form.valid || mutation.isPending}>
          {mutation.isPending ? "Збереження…" : student ? "Зберегти" : "Додати студента"}
        </Button>
      </DialogFooter>
    </form>
  );
}
