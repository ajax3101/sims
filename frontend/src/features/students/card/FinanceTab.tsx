import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useFinance, useSend } from "@/api/hooks";
import type { Contract } from "@/api/types";
import { TextField } from "@/components/Field";
import { SectionTitle, SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { Cipher } from "@/components/world/Cipher";
import { DemoMark } from "@/components/world/DemoMark";
import { SignalClip } from "@/components/world/Signal";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate, formatDebt, formatMoney, isPositive, todayIso } from "@/lib/format";
import { type InstalmentState, instalmentStates } from "@/lib/instalments";
import { markFresh } from "@/lib/fresh";
import { CONTRACT_STATUS, FUNDING, label } from "@/lib/labels";

export function FinanceTab({ studentId }: { studentId: string }) {
  const fin = useFinance(studentId);
  const [creating, setCreating] = useState(false);
  const [paying, setPaying] = useState<Contract | null>(null);
  if (fin.error) return <ErrorState error={fin.error} onRetry={() => fin.refetch()} />;
  if (!fin.data) return <Skeleton className="h-40 w-full" />;
  const { contracts, total_debt, funding } = fin.data;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-card px-5 py-4">
        <div className="flex flex-wrap items-center gap-x-8 gap-y-2 text-sm">
          <span><span className="text-muted-foreground">Фінансування:</span> <span className="font-medium">{label(FUNDING, funding)}</span></span>
          <span className="flex items-center gap-2">
            {isPositive(total_debt) && <SignalClip kind="tuition" />}
            <span className="text-muted-foreground">Заборгованість на сьогодні:</span>
            <span className="text-base font-semibold tabular">{formatDebt(total_debt)}</span>
          </span>
          <DemoMark />
        </div>
        <Button className="h-8" onClick={() => setCreating(true)}><Plus aria-hidden />Новий договір</Button>
      </div>

      {contracts.length === 0 ? (
        <p className="mt-6 rounded-md border border-dashed border-border bg-card px-5 py-6 text-sm text-muted-foreground">
          {funding === "contract" ? "Студент навчається за контрактом, але договору в системі ще немає." : "Договорів немає."}
        </p>
      ) : contracts.map((c) => (
        <section key={c.id} className="mt-8">
          <SectionTitle actions={<Button variant="outline" className="h-8" onClick={() => setPaying(c)}><Plus aria-hidden />Платіж</Button>}>
            Договір <Cipher>{c.number}</Cipher>
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              {label(CONTRACT_STATUS, c.status)} · {formatDate(c.starts_on)} – {formatDate(c.ends_on)} · сума {formatMoney(c.total_amount)}
            </span>
          </SectionTitle>
          <p className="mb-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
            <span><span className="text-muted-foreground">Нараховано на сьогодні</span> <span className="tabular">{formatMoney(c.due_total)}</span></span>
            <span><span className="text-muted-foreground">Сплачено</span> <span className="tabular">{formatMoney(c.paid_total)}</span></span>
            <span className="flex items-center gap-1.5">
              {isPositive(c.debt) && <SignalClip kind="tuition" />}
              <span className="text-muted-foreground">Борг</span>
              <span className={isPositive(c.debt) ? "font-semibold tabular" : "tabular"}>{formatDebt(c.debt)}</span>
            </span>
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            <SimpleTable caption="Графік оплат" rows={withStates(c)} rowKey={(s) => s.id} empty="Графік не задано."
              columns={[
                { header: "Строк оплати", className: "tabular", cell: (s) => formatDate(s.due_date) },
                { header: "Сума", className: "text-right tabular", cell: (s) => formatMoney(s.amount) },
                { header: "Стан", cell: (s) => <InstalmentBadge state={s.state} /> },
              ]} />
            <SimpleTable caption="Платежі" rows={c.payments} rowKey={(p) => p.id} empty="Платежів ще немає."
              columns={[
                { header: "Дата", className: "tabular", cell: (p) => formatDate(p.paid_on) },
                { header: "Сума", className: "text-right tabular", cell: (p) => formatMoney(p.amount) },
                { header: "Документ", cell: (p) => (p.external_ref ? <Cipher>{p.external_ref}</Cipher> : "—") },
              ]} />
          </div>
        </section>
      ))}

      <ContractDialog open={creating} onOpenChange={setCreating} studentId={studentId} />
      <PaymentDialog contract={paying} onClose={() => setPaying(null)} studentId={studentId} />
    </div>
  );
}

function withStates(c: Contract) {
  const states = instalmentStates(c.schedule, c.paid_total, todayIso());
  return c.schedule.map((s, i) => ({ ...s, state: states[i] }));
}

const INSTALMENT: Record<InstalmentState, { text: string; className: string }> = {
  paid: { text: "сплачено", className: "" },
  partial: { text: "сплачено частково", className: "font-medium" },
  overdue: { text: "прострочено", className: "font-medium text-destructive" },
  upcoming: { text: "очікується", className: "text-muted-foreground" },
};

function InstalmentBadge({ state }: { state: InstalmentState }) {
  return <span className={INSTALMENT[state].className}>{INSTALMENT[state].text}</span>;
}

interface Instalment { due_date: string; amount: string }

function ContractDialog({ open, onOpenChange, studentId }: { open: boolean; onOpenChange: (o: boolean) => void; studentId: string }) {
  const [number, setNumber] = useState("");
  const [startsOn, setStartsOn] = useState(todayIso());
  const [endsOn, setEndsOn] = useState("");
  const [total, setTotal] = useState("");
  const [schedule, setSchedule] = useState<Instalment[]>([{ due_date: "", amount: "" }]);
  const send = useSend<object, unknown>("POST", "/api/contracts", [["student", studentId], ["students"]]);
  const sum = schedule.reduce((acc, s) => acc + (Number(s.amount) || 0), 0);
  const totalNum = Number(total);
  const overflow = totalNum > 0 && sum > totalNum;
  const valid = number.trim() && totalNum > 0 && !overflow && schedule.every((s) => (s.due_date && Number(s.amount) > 0) || (!s.due_date && !s.amount));

  const setRow = (i: number, patch: Partial<Instalment>) => setSchedule(schedule.map((s, j) => (j === i ? { ...s, ...patch } : s)));
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form className="contents" onSubmit={(e) => {
          e.preventDefault();
          if (!valid) return;
          send.mutate({
            student_id: studentId, number: number.trim(), starts_on: startsOn, ends_on: endsOn || null, total_amount: total,
            schedule: schedule.filter((s) => s.due_date).map((s) => ({ due_date: s.due_date, amount: s.amount })),
          }, { onSuccess: () => { markFresh(studentId); toast.success(`Договір ${number} збережено`); onOpenChange(false); } });
        }}>
          <DialogHeader>
            <DialogTitle>Новий договір про навчання</DialogTitle>
            <DialogDescription>Борг рахується як сума платежів графіка, строк яких настав, мінус сплачене.</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <TextField label="№ договору" value={number} onChange={setNumber} required />
            <TextField label="Сума договору, ₴" value={total} onChange={setTotal} inputMode="decimal" required />
            <TextField label="Початок" type="date" value={startsOn} onChange={setStartsOn} required />
            <TextField label="Закінчення" type="date" value={endsOn} onChange={setEndsOn} />
          </div>
          <fieldset className="grid gap-2">
            <legend className="mb-1 text-xs font-medium text-muted-foreground">Графік оплат</legend>
            {schedule.map((s, i) => (
              <div key={i} className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
                <TextField label={`Строк ${i + 1}`} type="date" value={s.due_date} onChange={(v) => setRow(i, { due_date: v })} />
                <TextField label="Сума, ₴" value={s.amount} onChange={(v) => setRow(i, { amount: v })} inputMode="decimal" />
                <Button type="button" variant="ghost" size="icon-sm" aria-label={`Прибрати платіж ${i + 1}`}
                  onClick={() => setSchedule(schedule.filter((_, j) => j !== i))} disabled={schedule.length === 1}>
                  <Trash2 />
                </Button>
              </div>
            ))}
            <div className="flex items-center justify-between text-xs">
              <Button type="button" variant="ghost" size="sm" onClick={() => setSchedule([...schedule, { due_date: "", amount: "" }])}>
                <Plus aria-hidden />Ще платіж
              </Button>
              <span className={overflow ? "font-medium text-destructive" : "text-muted-foreground"}>
                Разом за графіком {formatMoney(sum)}{overflow ? " — більше за суму договору" : ""}
              </span>
            </div>
          </fieldset>
          {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>Скасувати</Button>
            <Button type="submit" disabled={!valid || send.isPending}>Зберегти договір</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function PaymentDialog({ contract, onClose, studentId }: { contract: Contract | null; onClose: () => void; studentId: string }) {
  const [paidOn, setPaidOn] = useState(todayIso());
  const [amount, setAmount] = useState("");
  const [ref, setRef] = useState("");
  const send = useSend<object, unknown>("POST", () => `/api/contracts/${contract?.id}/payments`, [["student", studentId], ["students"]]);
  return (
    <Dialog open={!!contract} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-md">
        {contract && (
          <form className="contents" onSubmit={(e) => {
            e.preventDefault();
            send.mutate({ paid_on: paidOn, amount, external_ref: ref || null, method: "bank" }, {
              onSuccess: () => { markFresh(studentId); toast.success(`Платіж ${formatMoney(amount)} внесено`); setAmount(""); setRef(""); onClose(); },
            });
          }}>
            <DialogHeader>
              <DialogTitle>Платіж за договором {contract.number}</DialogTitle>
              <DialogDescription>Поточний борг: {formatMoney(contract.debt)}</DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-3">
              <TextField label="Дата оплати" type="date" value={paidOn} onChange={setPaidOn} required />
              <TextField label="Сума, ₴" value={amount} onChange={setAmount} inputMode="decimal" required />
              <TextField label="№ платіжного документа" value={ref} onChange={setRef} className="col-span-2" hint="Повторний номер буде відхилено" />
            </div>
            {send.error && <p role="alert" className="text-sm text-destructive">{send.error.message}</p>}
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={onClose}>Скасувати</Button>
              <Button type="submit" disabled={!(Number(amount) > 0) || send.isPending}>Внести платіж</Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
