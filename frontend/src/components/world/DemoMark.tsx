import { FlaskConical } from "lucide-react";

import { useMeta } from "@/api/hooks";
import { cn } from "@/lib/utils";

/** Synthetic records must never pass for real ones: shown wherever demo grades, debts, contracts or curators appear. */
export function DemoMark({ className, tone = "light" }: { className?: string; tone?: "light" | "rail" }) {
  const meta = useMeta();
  if (!meta.data?.demo) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-sm px-1.5 py-px text-[0.6875rem] font-semibold tracking-wide uppercase",
        tone === "rail" ? "bg-signal-tuition text-course-ink" : "bg-signal-tuition/25 text-course-ink",
        className,
      )}
      title="Оцінки, борги, договори та куратори в цій базі синтетичні"
    >
      <FlaskConical className="size-3" aria-hidden />
      Демо-дані
    </span>
  );
}
