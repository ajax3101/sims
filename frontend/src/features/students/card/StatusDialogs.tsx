import { useState } from "react";
import { toast } from "sonner";

import { useAllGroups, useStudentMutation } from "@/api/hooks";
import type { Student } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { TextField } from "@/components/Field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { todayIso } from "@/lib/format";
import { STATUS, label } from "@/lib/labels";

type DialogProps = { open: boolean; onOpenChange: (o: boolean) => void; student: Student };

export function StatusDialog({ open, onOpenChange, student }: DialogProps) {
  const [status, setStatus] = useState("");
  const [date, setDate] = useState(todayIso());
  const [order, setOrder] = useState("");
  const [note, setNote] = useState("");
  const send = useStudentMutation<object>("POST", () => `/api/students/${student.id}/status`);
  const options = Object.entries(STATUS).filter(([v]) => v !== student.status).map(([value, l]) => ({ value, label: l }));
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form className="contents" onSubmit={(e) => {
          e.preventDefault();
          send.mutate({ status, changed_on: date, order_no: order || null, note: note || null }, {
            onSuccess: () => { toast.success(`Статус змінено: ${label(STATUS, status)}`); onOpenChange(false); setStatus(""); },
          });
        }}>
          <DialogHeader>
            <DialogTitle>Змінити статус</DialogTitle>
            <DialogDescription>Зараз: {label(STATUS, student.status)}. Зміна потрапить в історію студента.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <FilterSelect label="Новий статус" allLabel="Оберіть статус" value={status} onChange={setStatus} options={options} />
            <div className="grid grid-cols-2 gap-3">
              <TextField label="Дата" type="date" value={date} onChange={setDate} required />
              <TextField label="№ наказу" value={order} onChange={setOrder} />
            </div>
            <TextField label="Примітка" value={note} onChange={setNote} />
          </div>
          {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Скасувати</Button>
            <Button type="submit" disabled={!status || send.isPending}>Змінити статус</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function TransferDialog({ open, onOpenChange, student }: DialogProps) {
  const groups = useAllGroups();
  const [groupId, setGroupId] = useState("");
  const [date, setDate] = useState(todayIso());
  const [order, setOrder] = useState("");
  const send = useStudentMutation<object>("POST", () => `/api/students/${student.id}/transfer`);
  const options = (groups.data?.items ?? []).filter((g) => g.id !== student.group?.id).map((g) => ({ value: g.id, label: g.code }));
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form className="contents" onSubmit={(e) => {
          e.preventDefault();
          send.mutate({ group_id: groupId, on: date, order_ref: order || null }, {
            onSuccess: () => { toast.success("Студента переведено"); onOpenChange(false); setGroupId(""); },
          });
        }}>
          <DialogHeader>
            <DialogTitle>Перевести до іншої групи</DialogTitle>
            <DialogDescription>
              Поточне перебування {student.group ? `у групі ${student.group.code} ` : ""}закриється цією датою.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <FilterSelect label="Нова група" allLabel="Оберіть групу" value={groupId} onChange={setGroupId} options={options} />
            <div className="grid grid-cols-2 gap-3">
              <TextField label="Дата переведення" type="date" value={date} onChange={setDate} required />
              <TextField label="№ наказу" value={order} onChange={setOrder} />
            </div>
          </div>
          {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Скасувати</Button>
            <Button type="submit" disabled={!groupId || send.isPending}>Перевести</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
