import { formatMoney, isPositive } from "./format";

export type SignalKind = "academic" | "tuition" | "academic_leave" | "expelled" | "graduated";

export interface Signal {
  kind: SignalKind;
  label: string;
}

interface Signalled {
  status: string;
  has_academic_debt: boolean;
  financial_debt: string | number | null;
}

const STATUS_SIGNALS: Partial<Record<string, { kind: SignalKind; label: string }>> = {
  academic_leave: { kind: "academic_leave", label: "Академвідпустка" },
  expelled: { kind: "expelled", label: "Відрахований" },
  graduated: { kind: "graduated", label: "Випускник" },
};

/** Signals clipped to a record's visible margin, in reading order: what blocks progress first. */
export function signalsFor(s: Signalled): Signal[] {
  const out: Signal[] = [];
  if (s.has_academic_debt) out.push({ kind: "academic", label: "Академічна заборгованість" });
  if (isPositive(s.financial_debt)) out.push({ kind: "tuition", label: `Борг з оплати: ${formatMoney(s.financial_debt)}` });
  const status = STATUS_SIGNALS[s.status];
  if (status) out.push(status);
  return out;
}
