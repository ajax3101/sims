export function PageHeader({ title, meta, actions }: { title: string; meta?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3 px-6 pt-6 pb-4">
      <div className="min-w-0">
        <h1 className="text-[1.375rem] leading-tight font-semibold tracking-tight">{title}</h1>
        {meta && <div className="mt-1 text-sm text-muted-foreground">{meta}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
