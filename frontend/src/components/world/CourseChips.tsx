import { courseClass } from "@/lib/course";
import { cn } from "@/lib/utils";

/** Course filter as index tabs: every tab keeps its hue on its lower edge; the chosen one is filled with it. */
export function CourseChips({ value, onChange, label = "Курс" }: { value: string; onChange: (v: string) => void; label?: string }) {
  return (
    <div role="group" aria-label={label} className="flex h-8 items-stretch gap-1">
      <Chip active={!value} onClick={() => onChange("")} className="px-2.5">Усі</Chip>
      {[1, 2, 3, 4, 5, 6].map((c) => (
        <Chip key={c} course={c} active={value === String(c)} onClick={() => onChange(value === String(c) ? "" : String(c))}>
          {c}<span className="sr-only"> курс</span>
        </Chip>
      ))}
    </div>
  );
}

function Chip({ active, course, onClick, className, children }: {
  active: boolean; course?: number; onClick: () => void; className?: string; children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      style={course && !active ? { boxShadow: `inset 0 -3px 0 var(--course-${course})` } : undefined}
      className={cn(
        "relative min-w-8 rounded-md border text-sm font-medium tabular transition-colors duration-150",
        active
          ? cn("border-transparent text-course-ink shadow-[inset_0_-2px_0_oklch(0_0_0/0.12)]", course ? courseClass(course) : "bg-card")
          : "border-input bg-card/60 text-muted-foreground hover:bg-card hover:text-foreground",
        className,
      )}
    >
      {children}
    </button>
  );
}
