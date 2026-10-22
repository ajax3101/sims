import { cn } from "@/lib/utils";

export interface SimpleColumn<T> {
  header: string;
  cell: (row: T) => React.ReactNode;
  className?: string;
}

export function SimpleTable<T>({
  columns, rows, rowKey, empty, caption,
}: { columns: SimpleColumn<T>[]; rows: T[]; rowKey: (row: T) => string; empty: string; caption?: string }) {
  return (
    <div className="relative overflow-x-auto rounded-md border border-border bg-card">
      <table className="w-full border-collapse text-[0.875rem]">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="border-b border-border">
            {columns.map((c) => (
              <th key={c.header} scope="col" className={cn("h-9 px-3 text-left text-xs font-medium whitespace-nowrap text-muted-foreground", c.className)}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={columns.length} className="px-3 py-6 text-center text-sm text-muted-foreground">{empty}</td></tr>
          ) : rows.map((r) => (
            <tr key={rowKey(r)} className="border-b border-border/70 last:border-b-0">
              {columns.map((c) => <td key={c.header} className={cn("h-10 px-3 align-middle", c.className)}>{c.cell(r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SectionTitle({ children, actions }: { children: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="mt-8 mb-3 flex flex-wrap items-center justify-between gap-2 first:mt-0">
      <h2 className="text-base font-semibold">{children}</h2>
      {actions}
    </div>
  );
}
