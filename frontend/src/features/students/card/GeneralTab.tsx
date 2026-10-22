import type { Student } from "@/api/types";
import { Cipher } from "@/components/world/Cipher";
import { DemoMark } from "@/components/world/DemoMark";
import { formatDate } from "@/lib/format";
import { FORM, FUNDING, LEVEL, label } from "@/lib/labels";

export function GeneralTab({ student: s }: { student: Student }) {
  const g = s.group;
  const rows: [string, React.ReactNode][] = [
    ["Прізвище, ім’я, по батькові", s.full_name],
    ["Дата народження", formatDate(s.birth_date)],
    ["ІПН", s.tax_id ? <Cipher>{s.tax_id}</Cipher> : "—"],
    ["№ залікової книжки", s.record_book_no ? <Cipher>{s.record_book_no}</Cipher> : "—"],
    ["№ студентського квитка", s.student_card_no ? <Cipher>{s.student_card_no}</Cipher> : "—"],
    ["Дата зарахування", formatDate(s.enrolled_on)],
    ["Фінансування", s.funding_raw && s.funding === "other" ? `${label(FUNDING, s.funding)} (у списку: «${s.funding_raw}»)` : label(FUNDING, s.funding)],
    ["Телефон", s.contacts.phone ?? "—"],
    ["Email", s.contacts.email ? <a href={`mailto:${s.contacts.email}`} className="underline">{s.contacts.email}</a> : "—"],
  ];
  const study: [string, React.ReactNode][] = g ? [
    ["Підрозділ", g.org_unit.name],
    ["Освітній ступінь", label(LEVEL, g.level)],
    ["Форма здобуття освіти", label(FORM, g.form)],
    ["Спеціальність", `${g.specialty.code} ${g.specialty.name} (класифікатор ${g.specialty.classifier})`],
    ["Освітня програма", g.program?.name ?? "не вказано у списку"],
    ["Група", <Cipher key="g">{g.code}</Cipher>],
    ["Курс", g.course ? `${g.course}-й` : "—"],
    ["Рік вступу", g.is_shortened ? `${g.admission_year} (скорочений термін, вступ на ${g.entry_course}-й курс)` : String(g.admission_year)],
    ["Термін навчання", g.study_start ? `${formatDate(g.study_start)} – ${formatDate(g.study_end)}` : "—"],
    ["Куратор", g.curator ? <span key="c">{g.curator.full_name} <DemoMark className="ml-1" /></span> : "не призначено"],
  ] : [];
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Definition title="Особові дані" rows={rows} />
      {g && <Definition title="Навчання" rows={study} />}
    </div>
  );
}

function Definition({ title, rows }: { title: string; rows: [string, React.ReactNode][] }) {
  return (
    <section className="rounded-md border border-border bg-card px-5 py-4">
      <h2 className="mb-3 text-base font-semibold">{title}</h2>
      <dl className="grid grid-cols-[minmax(9rem,13rem)_1fr] gap-x-4 gap-y-2.5 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-muted-foreground">{k}</dt>
            <dd className="min-w-0 break-words">{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
