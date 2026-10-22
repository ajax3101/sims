import { AlertTriangle, SearchX } from "lucide-react";

import { Button } from "@/components/ui/button";

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-16 text-center">
      <SearchX className="size-6 text-muted-foreground" aria-hidden />
      <p className="font-medium">{title}</p>
      {hint && <p className="max-w-[46ch] text-sm text-muted-foreground">{hint}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : "Невідома помилка";
  return (
    <div role="alert" className="flex flex-col items-center gap-2 px-6 py-16 text-center">
      <AlertTriangle className="size-6 text-destructive" aria-hidden />
      <p className="font-medium">Не вдалося завантажити дані</p>
      <p className="max-w-[60ch] text-sm text-muted-foreground">{message}. Перевірте, чи запущено сервер API.</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-2" onClick={onRetry}>
          Спробувати ще раз
        </Button>
      )}
    </div>
  );
}
