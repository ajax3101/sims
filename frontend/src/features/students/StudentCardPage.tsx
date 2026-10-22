import { ArrowLeftRight, ChevronDown, ChevronLeft, FileDown, Pencil, Tag } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";

import { useFinance, useStudent } from "@/api/hooks";
import { ErrorState } from "@/components/States";
import { Cipher } from "@/components/world/Cipher";
import { CourseTab } from "@/components/world/CourseTab";
import { DemoMark } from "@/components/world/DemoMark";
import { SignalClip } from "@/components/world/Signal";
import { Button, buttonVariants } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { clearFresh } from "@/lib/fresh";
import { FORM, FUNDING, LEVEL, STATUS, label } from "@/lib/labels";
import { signalsFor } from "@/lib/signals";

import { FinanceTab } from "./card/FinanceTab";
import { GeneralTab } from "./card/GeneralTab";
import { HistoryTab } from "./card/HistoryTab";
import { PerformanceTab, usePerformanceSignal } from "./card/PerformanceTab";
import { StatusDialog, TransferDialog } from "./card/StatusDialogs";
import { StudentFormDialog } from "./StudentFormDialog";

const TABS = [
  { value: "general", label: "Загальні дані" },
  { value: "performance", label: "Успішність та заборгованості" },
  { value: "finance", label: "Оплати та контракти" },
  { value: "history", label: "Документи / Історія" },
] as const;

export function StudentCardPage() {
  const { id = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const tab = TABS.some((t) => t.value === params.get("tab")) ? params.get("tab")! : "general";
  const student = useStudent(id);
  const finance = useFinance(id);
  const hasAcademicDebt = usePerformanceSignal(id);
  const [dialog, setDialog] = useState<"edit" | "status" | "transfer" | null>(null);
  useEffect(() => clearFresh(id), [id]);

  if (student.error) return <ErrorState error={student.error} onRetry={() => student.refetch()} />;
  const s = student.data;
  const g = s?.group;
  const signals = s ? signalsFor({ status: s.status, has_academic_debt: hasAcademicDebt, financial_debt: finance.data?.total_debt ?? 0 }) : [];

  return (
    <div className="px-6 pt-4 pb-10">
      <Link to="/students" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft className="size-4" aria-hidden /> Реєстр студентів
      </Link>

      <div className="mt-4 pl-4"><CourseTab course={g?.course ?? null} raised /></div>
      <header className="rounded-md rounded-tl-none bg-card px-6 py-5 shadow-[0_8px_24px_-12px_oklch(0.2_0.03_165/0.3),0_1px_3px_oklch(0.2_0.03_165/0.1)]">
        <div className="flex items-start justify-between gap-4 max-lg:flex-wrap">
          <div className="min-w-0 flex-1">
            {s ? <h1 className="text-[1.5rem] leading-tight font-semibold tracking-tight">{s.full_name}</h1>
              : <Skeleton className="h-7 w-80" />}
            <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
              {g ? (
                <>
                  {/* each fact is unbreakable and carries the separator after it, so a wrapped line never starts with "·" */}
                  <span className="whitespace-nowrap">
                    <Link to={`/groups/${g.id}`} className="text-foreground hover:underline"><Cipher>{g.code}</Cipher></Link>
                    <span aria-hidden> ·</span>
                  </span>
                  {[`${g.specialty.code} ${g.specialty.name}`, g.program && `ОП «${g.program.name}»`,
                    `${label(LEVEL, g.level)}, ${label(FORM, g.form).toLowerCase()} форма`]
                    .filter((x): x is string => !!x)
                    .map((fact, i, all) => (
                      <span key={fact} className="whitespace-nowrap">{fact}{i < all.length - 1 && <span aria-hidden> ·</span>}</span>
                    ))}
                </>
              ) : s ? "Не зарахований до групи" : <Skeleton className="h-4 w-96" />}
            </p>
          </div>
          {s && (
            <div className="flex shrink-0 flex-wrap gap-2">
              <Button variant="outline" className="h-8" onClick={() => setDialog("edit")}><Pencil aria-hidden />Редагувати</Button>
              <Button variant="outline" className="h-8" onClick={() => setDialog("status")}><Tag aria-hidden />Змінити статус</Button>
              <Button variant="outline" className="h-8" onClick={() => setDialog("transfer")}><ArrowLeftRight aria-hidden />Перевести</Button>
              <DropdownMenu>
                <DropdownMenuTrigger className={buttonVariants({ variant: "outline", className: "h-8" })}>
                  <FileDown aria-hidden />Картка<ChevronDown data-icon="inline-end" aria-hidden />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {(["pdf", "docx", "xlsx"] as const).map((fmt) => (
                    <DropdownMenuItem key={fmt} render={<a href={`/api/reports/students/${id}/card?format=${fmt}`} />}>
                      Завантажити {fmt.toUpperCase()}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </div>
        {s && (
          <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-border pt-4 text-sm">
            <Fact label="Статус" value={label(STATUS, s.status)} />
            <Fact label="Фінансування" value={label(FUNDING, s.funding)} />
            <Fact label="Куратор" value={<>{g?.curator?.full_name ?? "не призначено"}{g?.curator && <DemoMark className="ml-2" />}</>} />
            <Fact label="№ залікової" value={s.record_book_no ? <Cipher>{s.record_book_no}</Cipher> : "—"} />
            {signals.length > 0 && (
              <ul aria-label="Сигнали" className="flex flex-wrap gap-x-4 gap-y-1">
                {signals.map((x) => (
                  <li key={x.kind} className="flex items-center gap-1.5 font-medium"><SignalClip kind={x.kind} />{x.label}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </header>

      <Tabs value={tab} onValueChange={(v) => setParams(v === "general" ? {} : { tab: String(v) }, { replace: true })} className="mt-6">
        <TabsList className="h-9">
          {TABS.map((t) => <TabsTrigger key={t.value} value={t.value} className="px-3">{t.label}</TabsTrigger>)}
        </TabsList>
        <TabsContent value="general" className="mt-4">{s && <GeneralTab student={s} />}</TabsContent>
        <TabsContent value="performance" className="mt-4">{s && <PerformanceTab student={s} />}</TabsContent>
        <TabsContent value="finance" className="mt-4">{s && <FinanceTab studentId={id} />}</TabsContent>
        <TabsContent value="history" className="mt-4"><HistoryTab studentId={id} /></TabsContent>
      </Tabs>

      {s && (
        <>
          <StudentFormDialog open={dialog === "edit"} onOpenChange={(o) => setDialog(o ? "edit" : null)} student={s} />
          <StatusDialog open={dialog === "status"} onOpenChange={(o) => setDialog(o ? "status" : null)} student={s} />
          <TransferDialog open={dialog === "transfer"} onOpenChange={(o) => setDialog(o ? "transfer" : null)} student={s} />
        </>
      )}
    </div>
  );
}

function Fact({ label: l, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-muted-foreground">{l}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
