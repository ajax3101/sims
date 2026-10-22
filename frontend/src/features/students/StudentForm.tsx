import { useState } from "react";

import { useAllGroups } from "@/api/hooks";
import type { Student } from "@/api/types";
import { FilterSelect } from "@/components/FilterSelect";
import { TextField } from "@/components/Field";
import { FUNDING } from "@/lib/labels";

export interface StudentFormValue {
  last_name: string;
  first_name: string;
  patronymic: string;
  group_id: string;
  funding: string;
  enrolled_on: string;
  record_book_no: string;
  student_card_no: string;
  tax_id: string;
  birth_date: string;
  phone: string;
  email: string;
}

export function emptyStudent(groupId = ""): StudentFormValue {
  return {
    last_name: "", first_name: "", patronymic: "", group_id: groupId, funding: "", enrolled_on: "",
    record_book_no: "", student_card_no: "", tax_id: "", birth_date: "", phone: "", email: "",
  };
}

export function fromStudent(s: Student): StudentFormValue {
  return {
    last_name: s.last_name, first_name: s.first_name, patronymic: s.patronymic ?? "", group_id: s.group?.id ?? "",
    funding: s.funding ?? "", enrolled_on: s.enrolled_on ?? "", record_book_no: s.record_book_no ?? "",
    student_card_no: s.student_card_no ?? "", tax_id: s.tax_id ?? "", birth_date: s.birth_date ?? "",
    phone: s.contacts.phone ?? "", email: s.contacts.email ?? "",
  };
}

/** API body: empty strings become nulls; contacts are nested. */
export function toBody(v: StudentFormValue, { withGroup }: { withGroup: boolean }) {
  const n = (x: string) => (x.trim() ? x.trim() : null);
  return {
    last_name: v.last_name.trim(), first_name: v.first_name.trim(), patronymic: n(v.patronymic),
    ...(withGroup ? { group_id: n(v.group_id) } : {}),
    funding: n(v.funding), enrolled_on: n(v.enrolled_on), record_book_no: n(v.record_book_no),
    student_card_no: n(v.student_card_no), tax_id: n(v.tax_id), birth_date: n(v.birth_date),
    contacts: Object.fromEntries(Object.entries({ phone: n(v.phone), email: n(v.email) }).filter(([, x]) => x)),
  };
}

export function StudentFields({
  value, onChange, showGroup, errors = {},
}: { value: StudentFormValue; onChange: (v: StudentFormValue) => void; showGroup: boolean; errors?: Partial<Record<keyof StudentFormValue, string>> }) {
  const groups = useAllGroups();
  const set = (k: keyof StudentFormValue) => (x: string) => onChange({ ...value, [k]: x });
  return (
    <div className="grid grid-cols-2 gap-3 max-sm:grid-cols-1">
      <TextField label="Прізвище" value={value.last_name} onChange={set("last_name")} required error={errors.last_name} autoFocus />
      <TextField label="Ім’я" value={value.first_name} onChange={set("first_name")} required error={errors.first_name} />
      <TextField label="По батькові" value={value.patronymic} onChange={set("patronymic")} />
      <FilterSelect label="Фінансування" allLabel="Не вказано" value={value.funding}
        options={Object.entries(FUNDING).map(([v, l]) => ({ value: v, label: l }))} onChange={set("funding")} />
      {showGroup && (
        <FilterSelect label="Група" allLabel="Без групи" value={value.group_id} className="col-span-2 max-sm:col-span-1"
          options={(groups.data?.items ?? []).map((g) => ({ value: g.id, label: g.code }))} onChange={set("group_id")} />
      )}
      <TextField label="Дата зарахування" type="date" value={value.enrolled_on} onChange={set("enrolled_on")} />
      <TextField label="Дата народження" type="date" value={value.birth_date} onChange={set("birth_date")} />
      <TextField label="№ залікової книжки" value={value.record_book_no} onChange={set("record_book_no")} />
      <TextField label="№ студентського квитка" value={value.student_card_no} onChange={set("student_card_no")} />
      <TextField label="ІПН" value={value.tax_id} onChange={set("tax_id")} inputMode="numeric" maxLength={10}
        hint="10 цифр" error={errors.tax_id} />
      <TextField label="Телефон" type="tel" value={value.phone} onChange={set("phone")} />
      <TextField label="Email" type="email" value={value.email} onChange={set("email")} className="col-span-2 max-sm:col-span-1" />
    </div>
  );
}

export function useStudentForm(initial: StudentFormValue) {
  const [value, setValue] = useState(initial);
  const errors: Partial<Record<keyof StudentFormValue, string>> = {};
  if (value.tax_id && !/^\d{10}$/.test(value.tax_id)) errors.tax_id = "ІПН має містити 10 цифр";
  const valid = !!value.last_name.trim() && !!value.first_name.trim() && !errors.tax_id;
  return { value, setValue, errors, valid };
}
