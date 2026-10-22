import { type ColumnDef, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { Link } from "react-router";

import type { StudentListItem } from "@/api/types";
import { Cipher } from "@/components/world/Cipher";
import { CourseTab } from "@/components/world/CourseTab";
import { SignalMargin } from "@/components/world/Signal";
import { Skeleton } from "@/components/ui/skeleton";
import { formatMoney, isPositive } from "@/lib/format";
import { isFresh } from "@/lib/fresh";
import { FUNDING, STATUS, label } from "@/lib/labels";
import { signalsFor } from "@/lib/signals";
import { cn } from "@/lib/utils";

type Col = ColumnDef<StudentListItem> & { meta?: { sort?: string; className?: string; headerLabel?: string } };

const columns: Col[] = [
  {
    id: "signals",
    header: () => <span className="sr-only">Сигнали</span>,
    cell: ({ row }) => <SignalMargin edge signals={signalsFor(row.original)} fresh={isFresh(row.original.id)} />,
    meta: { className: "relative w-14 pl-6 pr-0" },
  },
  {
    id: "name",
    header: "ПІБ",
    cell: ({ row }) => (
      <Link to={`/students/${row.original.id}`} onClick={(e) => e.stopPropagation()}
        className="font-medium text-foreground hover:underline focus-visible:underline">
        {row.original.full_name}
      </Link>
    ),
    meta: { sort: "name", className: "min-w-[16rem]" },
  },
  {
    id: "group",
    header: "Група",
    cell: ({ row }) => (row.original.group ? <Cipher>{row.original.group.code}</Cipher> : "—"),
    meta: { sort: "group", className: "whitespace-nowrap" },
  },
  {
    id: "course",
    header: "Курс",
    cell: ({ row }) => <CourseTab course={row.original.course} />,
    meta: { sort: "course", className: "w-16" },
  },
  {
    id: "specialty",
    header: "Спеціальність",
    cell: ({ row }) =>
      row.original.specialty ? (
        <span className="text-muted-foreground" title={row.original.specialty.name}>
          <span className="font-medium text-foreground">{row.original.specialty.code}</span> {row.original.specialty.name}
        </span>
      ) : "—",
    meta: { className: "max-w-[18rem] truncate" },
  },
  {
    id: "funding",
    header: "Фінансування",
    cell: ({ row }) => label(FUNDING, row.original.funding),
    meta: { sort: "funding" },
  },
  {
    id: "status",
    header: "Статус",
    cell: ({ row }) => (
      <span className={cn(row.original.status !== "active" && "font-medium")}>{label(STATUS, row.original.status)}</span>
    ),
    meta: { sort: "status" },
  },
  {
    id: "debt",
    header: "Борг з оплати",
    cell: ({ row }) =>
      isPositive(row.original.financial_debt) ? (
        <span className="font-medium">{formatMoney(row.original.financial_debt)}</span>
      ) : <span className="text-muted-foreground">—</span>,
    meta: { sort: "financial_debt", className: "pr-6 text-right" },
  },
];

export function StudentsTable({
  rows, sort, onSort, onOpen, onActivate, loading, selectedId,
}: {
  rows: StudentListItem[];
  sort: string;
  onSort: (column: string) => void;
  /** pull the row's card out (click, Space, ↑/↓) */
  onOpen: (row: StudentListItem) => void;
  /** Enter on a row */
  onActivate: (row: StudentListItem) => void;
  loading: boolean;
  selectedId?: string;
}) {
  const table = useReactTable({
    data: rows,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    manualPagination: true,
    getRowId: (r) => r.id,
  });
  const sortKey = sort.replace(/^-/, "");
  const desc = sort.startsWith("-");

  return (
    <div className="relative overflow-x-auto">
      <table className="w-full border-collapse text-[0.875rem]">
        <thead className="sticky top-0 z-10 bg-background">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id} className="border-b border-border">
              {hg.headers.map((h) => {
                const meta = (h.column.columnDef as Col).meta;
                const active = meta?.sort === sortKey;
                return (
                  <th key={h.id} scope="col"
                    aria-sort={active ? (desc ? "descending" : "ascending") : meta?.sort ? "none" : undefined}
                    className={cn("h-9 px-3 text-left text-xs font-medium whitespace-nowrap text-muted-foreground", meta?.className)}>
                    {meta?.sort ? (
                      <button type="button" onClick={() => onSort(meta.sort!)}
                        className={cn("-mx-1 inline-flex items-center gap-1 rounded px-1 py-0.5 hover:text-foreground",
                          active && "text-foreground", meta.className?.includes("text-right") && "flex-row-reverse")}>
                        {flexRender(h.column.columnDef.header, h.getContext())}
                        {active ? (desc ? <ArrowDown className="size-3.5" aria-hidden /> : <ArrowUp className="size-3.5" aria-hidden />)
                          : <ArrowUpDown className="size-3.5 opacity-40" aria-hidden />}
                      </button>
                    ) : flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody className={cn("transition-opacity duration-150", loading && rows.length > 0 && "opacity-60")}>
          {loading && rows.length === 0
            ? Array.from({ length: 12 }, (_, i) => (
                <tr key={i} className="border-b border-border/70">
                  <td className="py-2.5 pl-6"><Skeleton className="h-4 w-6" /></td>
                  {columns.slice(1).map((c) => (
                    <td key={c.id} className="px-3 py-2.5"><Skeleton className="h-4 w-full max-w-40" /></td>
                  ))}
                </tr>
              ))
            : table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  tabIndex={0}
                  aria-selected={row.id === selectedId}
                  onClick={() => onOpen(row.original)}
                  onKeyDown={(e) => {
                    const step = e.key === "ArrowDown" ? 1 : e.key === "ArrowUp" ? -1 : 0;
                    if (step) {
                      const target = e.currentTarget[step > 0 ? "nextElementSibling" : "previousElementSibling"] as HTMLElement | null;
                      const next = rows[row.index + step];
                      if (target && next) {
                        e.preventDefault();
                        target.focus();
                        onOpen(next);
                      }
                    } else if (e.key === "Enter") {
                      e.preventDefault();
                      onActivate(row.original);
                    } else if (e.key === " ") {
                      e.preventDefault();
                      onOpen(row.original);
                    }
                  }}
                  className={cn(
                    "cursor-pointer border-b border-border/70 bg-card transition-colors duration-100",
                    "hover:bg-accent/60 focus-visible:bg-accent/70 focus-visible:outline-offset-[-2px]",
                    row.id === selectedId && "bg-accent",
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className={cn("h-10 px-3 align-middle", (cell.column.columnDef as Col).meta?.className)}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  );
}
