const money = new Intl.NumberFormat("uk-UA", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** '10 000,00 ₴' — grouping with a plain space, as printed on Ukrainian forms. */
export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  return `${money.format(Number(value)).replace(/\s/g, " ")} ₴`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const [y, m, d] = value.slice(0, 10).split("-");
  return `${d}.${m}.${y}`;
}

export function isPositive(value: string | number | null | undefined): boolean {
  return value !== null && value !== undefined && Number(value) > 0;
}

/** Today's local date as an ISO date string (yyyy-mm-dd), for date inputs. */
export function todayIso(): string {
  return new Date().toLocaleDateString("en-CA");
}

/** A debt reads the same everywhere: an amount when owed, a dash when not. */
export function formatDebt(value: string | number | null | undefined): string {
  return isPositive(value) ? formatMoney(value) : "—";
}
