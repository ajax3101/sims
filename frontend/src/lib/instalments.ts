export type InstalmentState = "paid" | "partial" | "overdue" | "upcoming";

interface Instalment {
  due_date: string;
  amount: string;
}

/** Payments settle the oldest instalment first; what is left unpaid is overdue once its date has come. */
export function instalmentStates(schedule: Instalment[], paidTotal: string, today: string): InstalmentState[] {
  const order = schedule.map((s, i) => ({ s, i })).toSorted((a, b) => a.s.due_date.localeCompare(b.s.due_date));
  const states: InstalmentState[] = new Array(schedule.length);
  let remaining = Number(paidTotal) || 0;
  for (const { s, i } of order) {
    const amount = Number(s.amount);
    if (remaining >= amount) {
      states[i] = "paid";
      remaining -= amount;
    } else if (remaining > 0) {
      states[i] = "partial";
      remaining = 0;
    } else {
      states[i] = s.due_date <= today ? "overdue" : "upcoming";
    }
  }
  return states;
}
