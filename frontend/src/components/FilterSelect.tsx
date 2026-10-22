import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

const ALL = "__all";

export interface Option {
  value: string;
  label: string;
}

/** A labelled select whose empty value means "no filter". */
export function FilterSelect({
  label, value, options, onChange, allLabel = "Усі", className, triggerClassName,
}: {
  label: string;
  value: string | undefined;
  options: Option[];
  onChange: (value: string) => void;
  allLabel?: string;
  className?: string;
  triggerClassName?: string;
}) {
  const items = [{ value: ALL, label: allLabel }, ...options];
  return (
    <label className={cn("flex min-w-0 flex-col gap-1", className)}>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <Select
        items={items}
        value={value || ALL}
        onValueChange={(v) => onChange(!v || v === ALL ? "" : String(v))}
      >
        <SelectTrigger className={cn("h-8 w-full min-w-0 bg-card", triggerClassName)} aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="max-h-80">
          {items.map((o) => (
            <SelectItem key={o.value} value={o.value}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
