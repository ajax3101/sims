import { ArrowRight, Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { toast } from "sonner";

import { useSend, useSpecialties } from "@/api/hooks";
import type { SpecialtyRow } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { TextField } from "@/components/Field";
import { SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";

const CLASSIFIER = { "2024": "Перелік 2024", "2015": "Перелік 2015" } as const;

export function SpecialtiesTab() {
  const specs = useSpecialties();
  const [editing, setEditing] = useState<SpecialtyRow | "new" | null>(null);
  if (specs.error) return <ErrorState error={specs.error} onRetry={() => specs.refetch()} />;
  if (!specs.data) return <Skeleton className="h-64 w-full" />;
  return (
    <>
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Діють два переліки: старі коди (2015) ведуть до нових (2024) — так групи старого набору лишаються зіставними.
        </p>
        <Button className="h-8 shrink-0" onClick={() => setEditing("new")}><Plus aria-hidden />Нова спеціальність</Button>
      </div>
      <SimpleTable<SpecialtyRow>
        caption="Спеціальності" rows={specs.data} rowKey={(s) => s.id} empty="Спеціальностей немає."
        columns={[
          { header: "Код", className: "w-20", cell: (s) => <span className="font-semibold tabular">{s.code}</span> },
          { header: "Назва", cell: (s) => s.name },
          { header: "Перелік", className: "whitespace-nowrap text-muted-foreground", cell: (s) => CLASSIFIER[s.classifier] },
          {
            header: "Відповідає", className: "whitespace-nowrap",
            cell: (s) => (s.successor_code ? <span className="inline-flex items-center gap-1">{s.code}<ArrowRight className="size-3.5" aria-label="відповідає" />{s.successor_code}</span> : "—"),
          },
          { header: "Груп", className: "text-right tabular", cell: (s) => (s.groups_count ? <Link className="hover:underline" to={`/groups?specialty_id=${s.id}`}>{s.groups_count}</Link> : "—") },
          { header: "Студентів", className: "text-right tabular", cell: (s) => (s.students_count ? <Link className="hover:underline" to={`/students?specialty_id=${s.id}`}>{s.students_count}</Link> : "—") },
          { header: "", className: "w-12 text-right", cell: (s) => <Button variant="ghost" size="icon-sm" aria-label={`Редагувати ${s.code}`} onClick={() => setEditing(s)}><Pencil /></Button> },
        ]}
      />
      <SpecialtyDialog value={editing} onClose={() => setEditing(null)} all={specs.data} />
    </>
  );
}

function SpecialtyDialog({ value, onClose, all }: { value: SpecialtyRow | "new" | null; onClose: () => void; all: SpecialtyRow[] }) {
  const editing = value && value !== "new" ? value : null;
  return (
    <Dialog open={!!value} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-md">{value && <Form key={editing?.id ?? "new"} editing={editing} all={all} onDone={onClose} />}</DialogContent>
    </Dialog>
  );
}

function Form({ editing, all, onDone }: { editing: SpecialtyRow | null; all: SpecialtyRow[]; onDone: () => void }) {
  const [classifier, setClassifier] = useState<string>(editing?.classifier ?? "2024");
  const [code, setCode] = useState(editing?.code ?? "");
  const [name, setName] = useState(editing?.name ?? "");
  const [successor, setSuccessor] = useState(editing?.successor_id ?? "");
  const send = useSend<object, SpecialtyRow>(editing ? "PATCH" : "POST", editing ? `/api/specialties/${editing.id}` : "/api/specialties",
    [["specialties"], ["dictionaries"]]);
  const pattern = classifier === "2024" ? /^[A-Za-z]\d{1,2}$/ : /^\d{3}$/;
  const codeError = code && !pattern.test(code.trim()) ? (classifier === "2024" ? "Літера та 1–2 цифри, напр. G19" : "Три цифри, напр. 192") : undefined;
  const valid = name.trim().length >= 2 && (editing || (code && !codeError));
  return (
    <form className="contents" onSubmit={(e) => {
      e.preventDefault();
      const body = editing ? { name: name.trim(), successor_id: successor || null } : { classifier, code: code.trim(), name: name.trim(), successor_id: successor || null };
      send.mutate(body, { onSuccess: (s) => { toast.success(`Спеціальність ${s.code} збережено`); onDone(); } });
    }}>
      <DialogHeader>
        <DialogTitle>{editing ? `Спеціальність ${editing.code}` : "Нова спеціальність"}</DialogTitle>
        <DialogDescription>{editing ? "Код і перелік не змінюються: на них посилаються шифри груп." : "Галузь знань визначиться з коду автоматично."}</DialogDescription>
      </DialogHeader>
      <div className="grid grid-cols-2 gap-3">
        {!editing && (
          <>
            <FilterSelect label="Перелік" allLabel="—" value={classifier} onChange={(v) => setClassifier(v || "2024")}
              options={Object.entries(CLASSIFIER).map(([value, label]) => ({ value, label }))} />
            <TextField label="Код" value={code} onChange={setCode} required error={codeError} autoFocus />
          </>
        )}
        <TextField label="Назва" value={name} onChange={setName} required className="col-span-2" />
        {(editing?.classifier ?? classifier) === "2015" && (
          <FilterSelect label="Відповідає спеціальності 2024" allLabel="Не вказано" value={successor} onChange={setSuccessor} className="col-span-2"
            options={all.filter((s) => s.classifier === "2024").map((s) => ({ value: s.id, label: `${s.code} · ${s.name}` }))} />
        )}
      </div>
      {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>Скасувати</Button>
        <Button type="submit" disabled={!valid || send.isPending}>Зберегти</Button>
      </DialogFooter>
    </form>
  );
}
