import { Link } from "react-router";

import { useHistory } from "@/api/hooks";
import { SectionTitle, SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { Cipher } from "@/components/world/Cipher";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/format";
import { MEMBERSHIP_REASON, STATUS, label } from "@/lib/labels";

export function HistoryTab({ studentId }: { studentId: string }) {
  const h = useHistory(studentId);
  if (h.error) return <ErrorState error={h.error} onRetry={() => h.refetch()} />;
  if (!h.data) return <Skeleton className="h-40 w-full" />;
  return (
    <div>
      <SectionTitle>Перебування в групах</SectionTitle>
      <SimpleTable caption="Перебування в групах" rows={h.data.memberships} rowKey={(m) => `${m.group.id}-${m.starts_on}`} empty="Записів немає."
        columns={[
          { header: "Група", cell: (m) => <Link to={`/groups/${m.group.id}`} className="hover:underline"><Cipher>{m.group.code}</Cipher></Link> },
          { header: "Підстава", cell: (m) => label(MEMBERSHIP_REASON, m.reason) },
          { header: "З", className: "tabular", cell: (m) => formatDate(m.starts_on) },
          { header: "По", className: "tabular", cell: (m) => (m.ends_on ? formatDate(m.ends_on) : <span className="font-medium">дотепер</span>) },
          { header: "Наказ", cell: (m) => m.order_ref ?? "—" },
        ]} />
      <SectionTitle>Зміни статусу</SectionTitle>
      <SimpleTable caption="Зміни статусу" rows={h.data.status_history} rowKey={(s) => `${s.status}-${s.changed_on}`} empty="Статус не змінювався."
        columns={[
          { header: "Дата", className: "tabular", cell: (s) => formatDate(s.changed_on) },
          { header: "Статус", cell: (s) => <span className="font-medium">{label(STATUS, s.status)}</span> },
          { header: "Наказ", cell: (s) => s.order_no ?? "—" },
          { header: "Примітка", cell: (s) => s.note ?? "—" },
        ]} />
      <SectionTitle>Документи</SectionTitle>
      <SimpleTable caption="Документи" rows={h.data.documents} rowKey={(d) => d.id} empty="Документів не додано."
        columns={[
          { header: "Документ", cell: (d) => d.title },
          { header: "Дата", className: "tabular", cell: (d) => formatDate(d.issued_on) },
        ]} />
    </div>
  );
}
