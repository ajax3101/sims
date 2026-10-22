import { courseClass } from "@/lib/course";
import { cn } from "@/lib/utils";

/** An index tab in the course's colour; `raised` is the tab standing proud of a pulled card's top edge. */
export function CourseTab({ course, raised, className }: { course: number | null; raised?: boolean; className?: string }) {
  const text = course ? `${course} курс` : "курс —";
  return (
    <span
      className={cn(
        "inline-flex items-center font-medium text-course-ink tabular",
        raised ? "rounded-t-md px-3 pt-1 pb-1.5 text-xs shadow-[0_-1px_2px_oklch(0_0_0/0.08)]" : "rounded-sm px-1.5 py-px text-xs",
        courseClass(course),
        className,
      )}
    >
      {raised ? text : (course ?? "—")}
      {!raised && <span className="sr-only"> курс</span>}
    </span>
  );
}
