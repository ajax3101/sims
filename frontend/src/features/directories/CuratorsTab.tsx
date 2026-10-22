import { Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { toast } from "sonner";

import { useDictionaries, useSend, useStaffDirectory } from "@/api/hooks";
import type { Staff } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { TextField } from "@/components/Field";
import { SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { Cipher } from "@/components/world/Cipher";
import { DemoMark } from "@/components/world/DemoMark";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export function CuratorsTab() {
  const [q, setQ] = useState("");
  const [active, setActive] = useState("true");
  const staff = useStaffDirectory(q, active);
  const [editing, setEditing] = useState<Staff | "new" | null>(null);
  return (
    <>
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap items-end gap-3">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Прізвище, ім’я" aria-label="Пошук співробітника" className="h-8 w-64 bg-card" />
          <FilterSelect label="Стан" allLabel="Усі" value={active} onChange={setActive} className="w-40"
            options={[{ value: "true", label: "Працюють" }, { value: "false", label: "Не працюють" }]} />
          <DemoMark className="mb-1.5" />
        </div>
        <Button className="h-8" onClick={() => setEditing("new")}><Plus aria-hidden />Новий куратор</Button>
      </div>
      {staff.error ? <ErrorState error={staff.error} onRetry={() => staff.refetch()} />
        : !staff.data ? <Skeleton className="h-64 w-full" />
        : (
          <SimpleTable<Staff>
            caption="Куратори та співробітники" rows={staff.data.items} rowKey={(s) => s.id}
            empty="Нікого не знайдено. Додайте куратора — потім призначте його групі на сторінці групи."
            columns={[
              { header: "ПІБ", className: "whitespace-nowrap", cell: (s) => <span className="font-medium">{s.full_name}</span> },
              { header: "Посада", cell: (s) => [s.position, s.academic_degree].filter(Boolean).join(", ") || "—" },
              {
                header: "Курує групи",
                cell: (s) => s.curated_groups.length
                  ? <span className="flex flex-wrap gap-x-2">{s.curated_groups.map((g) => <Link key={g.id} to={`/groups/${g.id}`} className="hover:underline"><Cipher>{g.code}</Cipher></Link>)}</span>
                  : <span className="text-muted-foreground">—</span>,
              },
              { header: "Контакти", className: "text-muted-foreground", cell: (s) => [s.email, s.phone].filter(Boolean).join(" · ") || "—" },
              { header: "", className: "w-12 text-right", cell: (s) => <Button variant="ghost" size="icon-sm" aria-label={`Редагувати ${s.full_name}`} onClick={() => setEditing(s)}><Pencil /></Button> },
            ]}
          />
        )}
      <StaffDialog value={editing} onClose={() => setEditing(null)} />
    </>
  );
}

function StaffDialog({ value, onClose }: { value: Staff | "new" | null; onClose: () => void }) {
  const editing = value && value !== "new" ? value : null;
  return (
    <Dialog open={!!value} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">{value && <Form key={editing?.id ?? "new"} editing={editing} onDone={onClose} />}</DialogContent>
    </Dialog>
  );
}

function Form({ editing, onDone }: { editing: Staff | null; onDone: () => void }) {
  const dict = useDictionaries();
  const [v, setV] = useState({
    last_name: editing?.last_name ?? "", first_name: editing?.first_name ?? "", patronymic: editing?.patronymic ?? "",
    position: editing?.position ?? "", academic_degree: editing?.academic_degree ?? "", org_unit_id: editing?.org_unit_id ?? "",
    email: editing?.email ?? "", phone: editing?.phone ?? "", is_active: editing?.is_active ?? true,
  });
  const set = (k: keyof typeof v) => (x: string) => setV({ ...v, [k]: x });
  const send = useSend<object, Staff>(editing ? "PATCH" : "POST", editing ? `/api/staff/${editing.id}` : "/api/staff", [["staff"], ["groups"], ["group"]]);
  const emailError = v.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v.email) ? "Перевірте адресу" : undefined;
  const valid = v.last_name.trim() && v.first_name.trim() && !emailError;
  const n = (x: string) => x.trim() || null;
  return (
    <form className="contents" onSubmit={(e) => {
      e.preventDefault();
      send.mutate({
        last_name: v.last_name.trim(), first_name: v.first_name.trim(), patronymic: n(v.patronymic), position: n(v.position),
        academic_degree: n(v.academic_degree), org_unit_id: v.org_unit_id || null, email: n(v.email), phone: n(v.phone),
        ...(editing ? { is_active: v.is_active } : {}),
      }, { onSuccess: (s) => { toast.success(`${s.full_name}: збережено`); onDone(); } });
    }}>
      <DialogHeader>
        <DialogTitle>{editing ? editing.full_name : "Новий куратор"}</DialogTitle>
        <DialogDescription>Групу куратору призначають на сторінці групи — так зберігається історія кураторства.</DialogDescription>
      </DialogHeader>
      <div className="grid grid-cols-2 gap-3 max-sm:grid-cols-1">
        <TextField label="Прізвище" value={v.last_name} onChange={set("last_name")} required autoFocus />
        <TextField label="Ім’я" value={v.first_name} onChange={set("first_name")} required />
        <TextField label="По батькові" value={v.patronymic} onChange={set("patronymic")} />
        <TextField label="Посада" value={v.position} onChange={set("position")} placeholder="доцент кафедри…" />
        <TextField label="Науковий ступінь" value={v.academic_degree} onChange={set("academic_degree")} placeholder="к.т.н." />
        <FilterSelect label="Підрозділ" allLabel="Не вказано" value={v.org_unit_id} onChange={set("org_unit_id")}
          options={(dict.data?.org_units ?? []).map((u) => ({ value: u.id, label: u.name }))} />
        <TextField label="Email" type="email" value={v.email} onChange={set("email")} error={emailError} />
        <TextField label="Телефон" type="tel" value={v.phone} onChange={set("phone")} />
        {editing && (
          <label className="col-span-2 flex items-center gap-2 text-sm max-sm:col-span-1">
            <input type="checkbox" checked={v.is_active} onChange={(e) => setV({ ...v, is_active: e.target.checked })} className="size-4 accent-[var(--primary)]" />
            Працює (неактивних не пропонують у куратори)
          </label>
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
