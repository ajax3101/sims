import { ArrowRight, FileDown, X } from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router";

import type { StudentListItem } from "@/api/types";
import { Cipher } from "@/components/world/Cipher";
import { CourseTab } from "@/components/world/CourseTab";
import { SignalClip } from "@/components/world/Signal";
import { Button, buttonVariants } from "@/components/ui/button";
import { clearFresh } from "@/lib/fresh";
import { FUNDING, STATUS, label } from "@/lib/labels";
import { signalsFor } from "@/lib/signals";

/**
 * The signature move: a row's card is pulled out of the file — index tab first — beside a register that stays live.
 * Non-modal on purpose: ↑/↓ on the rows flips to the neighbouring card, Enter opens the full card, Esc puts it back.
 */
export function StudentPeek({ student, onClose }: { student: StudentListItem | null; onClose: () => void }) {
  useEffect(() => {
    if (!student) return;
    clearFresh(student.id);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !document.querySelector("[role=dialog][data-open]")) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [student, onClose]);

  if (!student) return null;
  const signals = signalsFor(student);
  return (
    <aside
      aria-label={`Картка: ${student.full_name}`}
      className="fixed top-20 right-5 z-30 w-[24rem] max-w-[calc(100vw-2.5rem)] animate-in fade-in-0 slide-in-from-right-6 duration-200 ease-out"
    >
      <div className="pl-5"><CourseTab course={student.course} raised /></div>
      <div className="rounded-md rounded-tl-none bg-card shadow-[0_14px_36px_-10px_oklch(0.2_0.03_165/0.38),0_2px_6px_oklch(0.2_0.03_165/0.12)]">
        <div className="relative border-b border-border px-5 pt-4 pb-4 pr-12">
          <h2 className="text-lg leading-snug font-semibold">{student.full_name}</h2>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
            {student.group ? <Cipher className="text-foreground">{student.group.code}</Cipher> : "без групи"}
            {student.specialty && <span>· {student.specialty.code} {student.specialty.name}</span>}
          </p>
          <Button variant="ghost" size="icon-sm" onClick={onClose} aria-label="Закрити картку (Esc)" className="absolute top-3 right-3">
            <X />
          </Button>
        </div>

        <section aria-label="Сигнали" className="border-b border-border px-5 py-3.5">
          {signals.length ? (
            <ul className="flex flex-col gap-2">
              {signals.map((s) => (
                <li key={s.kind} className="flex items-center gap-2.5 text-sm"><SignalClip kind={s.kind} />{s.label}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Заборгованостей немає.</p>
          )}
        </section>

        <dl className="grid grid-cols-[8.5rem_1fr] gap-x-3 gap-y-2 px-5 py-3.5 text-sm">
          <dt className="text-muted-foreground">Статус</dt>
          <dd>{label(STATUS, student.status)}</dd>
          <dt className="text-muted-foreground">Фінансування</dt>
          <dd>{label(FUNDING, student.funding)}</dd>
          <dt className="text-muted-foreground">№ залікової</dt>
          <dd>{student.record_book_no ? <Cipher>{student.record_book_no}</Cipher> : "—"}</dd>
        </dl>

        <div className="flex flex-wrap items-center gap-2 border-t border-border px-5 py-3.5">
          <Link to={`/students/${student.id}`} className={buttonVariants({ className: "h-8" })}>
            Відкрити картку
            <ArrowRight data-icon="inline-end" aria-hidden />
          </Link>
          <a href={`/api/reports/students/${student.id}/card?format=pdf`} className={buttonVariants({ variant: "outline", className: "h-8" })}>
            <FileDown aria-hidden />
            Картка PDF
          </a>
          <span className="ml-auto text-xs text-muted-foreground max-sm:hidden">↑↓ гортати · Enter відкрити</span>
        </div>
      </div>
    </aside>
  );
}
