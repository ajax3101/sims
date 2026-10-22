import { useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";

import { useDictionaries, useSend } from "@/api/hooks";
import type { Group } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { TextField } from "@/components/Field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { FORM, LEVEL } from "@/lib/labels";

const STATUS = { active: "Навчається", graduated: "Випущена", archived: "В архіві" };
const opts = (m: Record<string, string>) => Object.entries(m).map(([value, label]) => ({ value, label }));

/** Create a group (cipher parsed server-side into cohort facts) or edit an existing one. */
export function GroupDialog({ open, onOpenChange, group }: { open: boolean; onOpenChange: (o: boolean) => void; group?: Group }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">{open && <Body group={group} onDone={() => onOpenChange(false)} />}</DialogContent>
    </Dialog>
  );
}

function Body({ group, onDone }: { group?: Group; onDone: () => void }) {
  const dict = useDictionaries();
  const navigate = useNavigate();
  const units = (dict.data?.org_units ?? []).filter((u) => u.kind !== "department");
  const [v, setV] = useState({
    code: group?.code ?? "", specialty_id: group?.specialty.id ?? "", level: group?.level ?? "bachelor",
    form: group?.form ?? "part_time", program_id: group?.program?.id ?? "", org_unit_id: group?.org_unit.id ?? "",
    study_start: group?.study_start ?? "", study_end: group?.study_end ?? "", status: group?.status ?? "active",
  });
  const set = (k: keyof typeof v) => (x: string) => setV({ ...v, [k]: x });
  const orgUnit = v.org_unit_id || (units.length === 1 ? units[0].id : "");
  const level = dict.data?.levels.find((l) => l.code === v.level);
  const programs = (dict.data?.programs ?? []).filter((p) => p.specialty_id === v.specialty_id && p.level_id === level?.id);
  const send = useSend<object, Group>(group ? "PATCH" : "POST", group ? `/api/groups/${group.id}` : "/api/groups",
    [["groups"], ["group"], ["students"], ["specialties"]]);
  const n = (x: string) => x || null;
  const valid = group ? true : v.code.trim() && v.specialty_id && orgUnit;

  return (
    <form className="contents" onSubmit={(e) => {
      e.preventDefault();
      const body = group
        ? { program_id: n(v.program_id), org_unit_id: orgUnit, study_start: n(v.study_start), study_end: n(v.study_end), status: v.status }
        : { code: v.code.trim(), specialty_id: v.specialty_id, level: v.level, form: v.form, program_id: n(v.program_id),
            org_unit_id: orgUnit, study_start: n(v.study_start), study_end: n(v.study_end) };
      send.mutate(body, {
        onSuccess: (g) => { toast.success(group ? "Групу збережено" : `Групу ${g.code} створено`); onDone(); if (!group) navigate(`/groups/${g.id}`); },
      });
    }}>
      <DialogHeader>
        <DialogTitle>{group ? `Група ${group.code}` : "Нова група"}</DialogTitle>
        <DialogDescription>
          {group ? "Шифр, спеціальність і рівень визначають когорту, тому їх не редагують." : "Рік вступу та курс вступу (с2) система визначить із шифру, напр. 6.G19.26-з-пцб-с2."}
        </DialogDescription>
      </DialogHeader>
      <div className="grid grid-cols-2 gap-3 max-sm:grid-cols-1">
        {!group && <TextField label="Шифр групи" value={v.code} onChange={set("code")} required autoFocus className="col-span-2 max-sm:col-span-1" />}
        {!group && (
          <>
            <FilterSelect label="Спеціальність" allLabel="Оберіть" value={v.specialty_id} onChange={(x) => setV({ ...v, specialty_id: x, program_id: "" })}
              className="col-span-2 max-sm:col-span-1"
              options={(dict.data?.specialties ?? []).map((s) => ({ value: s.id, label: `${s.code} · ${s.name}` }))} />
            <FilterSelect label="Рівень" allLabel="—" value={v.level} onChange={(x) => setV({ ...v, level: x || "bachelor", program_id: "" })} options={opts(LEVEL)} />
            <FilterSelect label="Форма" allLabel="—" value={v.form} onChange={(x) => set("form")(x || "part_time")} options={opts(FORM)} />
          </>
        )}
        <FilterSelect label="Освітня програма" allLabel={programs.length ? "Не вказано" : "Немає ОП для цієї спеціальності"} value={v.program_id}
          onChange={set("program_id")} className="col-span-2 max-sm:col-span-1"
          options={(group ? (dict.data?.programs ?? []).filter((p) => p.specialty_id === group.specialty.id) : programs).map((p) => ({ value: p.id, label: p.name }))} />
        <FilterSelect label="Підрозділ" allLabel="Оберіть" value={orgUnit} onChange={set("org_unit_id")} className="col-span-2 max-sm:col-span-1"
          options={units.map((u) => ({ value: u.id, label: u.name }))} />
        <TextField label="Початок навчання" type="date" value={v.study_start} onChange={set("study_start")} />
        <TextField label="Кінець навчання" type="date" value={v.study_end} onChange={set("study_end")} />
        {group && <FilterSelect label="Стан групи" allLabel="—" value={v.status} onChange={(x) => set("status")(x || "active")} options={opts(STATUS)} />}
      </div>
      {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onDone}>Скасувати</Button>
        <Button type="submit" disabled={!valid || send.isPending}>{group ? "Зберегти" : "Створити групу"}</Button>
      </DialogFooter>
    </form>
  );
}
