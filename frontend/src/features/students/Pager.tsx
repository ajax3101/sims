import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PAGE_SIZES } from "@/lib/studentQuery";

export function Pager({
  page, size, total, onPage, onSize,
}: { page: number; size: number; total: number; onPage: (p: number) => void; onSize: (s: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / size));
  const from = total ? (page - 1) * size + 1 : 0;
  const to = Math.min(page * size, total);
  const items = PAGE_SIZES.map((s) => ({ value: String(s), label: `${s} на сторінці` }));
  return (
    <nav aria-label="Сторінки" className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 text-sm text-muted-foreground">
      <span className="tabular" aria-live="polite">{from}–{to} з {total}</span>
      <div className="flex items-center gap-2">
        <Select items={items} value={String(size)} onValueChange={(v) => onSize(Number(v))}>
          <SelectTrigger className="h-8 w-40 bg-card" aria-label="Записів на сторінці"><SelectValue /></SelectTrigger>
          <SelectContent>
            {items.map((i) => <SelectItem key={i.value} value={i.value}>{i.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button variant="outline" size="icon-sm" onClick={() => onPage(page - 1)} disabled={page <= 1} aria-label="Попередня сторінка">
          <ChevronLeft />
        </Button>
        <span className="tabular text-foreground">{page} / {pages}</span>
        <Button variant="outline" size="icon-sm" onClick={() => onPage(page + 1)} disabled={page >= pages} aria-label="Наступна сторінка">
          <ChevronRight />
        </Button>
      </div>
    </nav>
  );
}
