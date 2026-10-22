import { Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { useAllGroups } from "@/api/hooks";
import type { Group } from "@/api/types";
import { SimpleTable } from "@/components/SimpleTable";
import { ErrorState } from "@/components/States";
import { Cipher } from "@/components/world/Cipher";
import { CourseTab } from "@/components/world/CourseTab";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/format";
import { FORM, LEVEL, label } from "@/lib/labels";

import { GroupDialog } from "../groups/GroupDialog";

export function GroupsTab() {
  const groups = useAllGroups();
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState<Group | "new" | null>(null);
  if (groups.error) return <ErrorState error={groups.error} onRetry={() => groups.refetch()} />;
  if (!groups.data) return <Skeleton className="h-64 w-full" />;
  const rows = groups.data.items.filter((g) => !q || g.code.toLowerCase().includes(q.toLowerCase()) || g.code_norm.toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <div className="mb-3 flex items-center justify-between gap-3">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Шифр групи" aria-label="Пошук групи" className="h-8 w-64 bg-card" />
        <Button className="h-8" onClick={() => setEditing("new")}><Plus aria-hidden />Нова група</Button>
      </div>
      <SimpleTable<Group>
        caption="Групи" rows={rows} rowKey={(g) => g.id} empty="Груп не знайдено."
        columns={[
          { header: "Шифр", className: "whitespace-nowrap", cell: (g) => <Link to={`/groups/${g.id}`} className="font-medium hover:underline"><Cipher>{g.code}</Cipher></Link> },
          { header: "Курс", cell: (g) => <CourseTab course={g.course} /> },
          { header: "Спеціальність", cell: (g) => <span className="block max-w-[18rem] truncate" title={g.specialty.name}><span className="font-semibold">{g.specialty.code}</span> {g.specialty.name}</span> },
          { header: "Рівень / форма", className: "whitespace-nowrap", cell: (g) => `${label(LEVEL, g.level)}, ${label(FORM, g.form).toLowerCase()}` },
          { header: "Рік вступу", className: "tabular", cell: (g) => (g.is_shortened ? `${g.admission_year}, с2` : g.admission_year) },
          { header: "Термін", className: "whitespace-nowrap tabular", cell: (g) => (g.study_start ? `${formatDate(g.study_start)} – ${formatDate(g.study_end)}` : "—") },
          { header: "", className: "w-12 text-right", cell: (g) => <Button variant="ghost" size="icon-sm" aria-label={`Редагувати ${g.code}`} onClick={() => setEditing(g)}><Pencil /></Button> },
        ]}
      />
      <GroupDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} group={editing && editing !== "new" ? editing : undefined} />
    </>
  );
}
