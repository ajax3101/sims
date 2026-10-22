import { cn } from "@/lib/utils";
import type { Signal as SignalT, SignalKind } from "@/lib/signals";

const FILL: Record<SignalKind | "fresh", string> = {
  academic: "fill-signal-academic",
  tuition: "fill-signal-tuition",
  academic_leave: "fill-signal-leave",
  expelled: "fill-signal-expelled",
  graduated: "fill-signal-graduated",
  fresh: "fill-signal-fresh",
};

/** A flat signal clip: the short leg folds over the card's top edge, the long leg hangs down its face. */
export function SignalClip({ kind, className }: { kind: SignalKind | "fresh"; className?: string }) {
  const hollow = kind === "fresh";
  return (
    <svg viewBox="0 0 8 16" aria-hidden className={cn("h-4 w-2 shrink-0", className)}>
      <path
        d="M0 0h8v15a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1z"
        className={hollow ? "fill-card stroke-signal-fresh" : FILL[kind]}
        strokeWidth={hollow ? 1.5 : 0}
      />
    </svg>
  );
}

/**
 * The visible margin of a record. `edge` clips the signals onto the row's top edge (register rows);
 * otherwise they sit inline beside a label.
 */
export function SignalMargin({ signals, fresh, edge, className }: { signals: SignalT[]; fresh?: boolean; edge?: boolean; className?: string }) {
  const labels = [...(fresh ? ["Змінено в цій сесії"] : []), ...signals.map((s) => s.label)];
  return (
    <span
      className={cn("flex items-start gap-[3px]", edge && "absolute top-[-1px] left-6", className)}
      role={labels.length ? "img" : undefined}
      aria-label={labels.length ? labels.join("; ") : undefined}
      title={labels.length ? labels.join("\n") : undefined}
    >
      {fresh && <SignalClip kind="fresh" />}
      {signals.map((s) => (
        <SignalClip key={s.kind} kind={s.kind} />
      ))}
    </span>
  );
}
