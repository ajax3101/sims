import { useId } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export function Field({
  label, hint, error, className, children,
}: { label: string; hint?: string; error?: string; className?: string; children: (id: string) => React.ReactNode }) {
  const id = useId();
  return (
    <div className={cn("flex min-w-0 flex-col gap-1", className)}>
      <label htmlFor={id} className="text-xs font-medium text-muted-foreground">{label}</label>
      {children(id)}
      {error ? <p className="text-xs text-destructive">{error}</p> : hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function TextField({
  label, value, onChange, hint, error, className, ...rest
}: { label: string; value: string; onChange: (v: string) => void; hint?: string; error?: string; className?: string }
  & Omit<React.ComponentProps<"input">, "value" | "onChange">) {
  return (
    <Field label={label} hint={hint} error={error} className={className}>
      {(id) => <Input id={id} value={value} onChange={(e) => onChange(e.target.value)} aria-invalid={!!error} className="h-8 bg-card" {...rest} />}
    </Field>
  );
}
