import { useSearchParams } from "react-router";

import { PageHeader } from "@/components/PageHeader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { CuratorsTab } from "./CuratorsTab";
import { GroupsTab } from "./GroupsTab";
import { SpecialtiesTab } from "./SpecialtiesTab";

const TABS = [
  { value: "specialties", label: "Спеціальності" },
  { value: "groups", label: "Групи" },
  { value: "curators", label: "Куратори" },
] as const;

export function DirectoriesPage() {
  const [params, setParams] = useSearchParams();
  const tab = TABS.some((t) => t.value === params.get("tab")) ? params.get("tab")! : "specialties";
  return (
    <>
      <PageHeader title="Довідники" meta="Спеціальності, групи та куратори, з яких складаються картки студентів" />
      <Tabs value={tab} onValueChange={(v) => setParams({ tab: String(v) }, { replace: true })} className="px-6 pb-10">
        <TabsList className="h-9">
          {TABS.map((t) => <TabsTrigger key={t.value} value={t.value} className="px-4">{t.label}</TabsTrigger>)}
        </TabsList>
        <TabsContent value="specialties" className="mt-4"><SpecialtiesTab /></TabsContent>
        <TabsContent value="groups" className="mt-4"><GroupsTab /></TabsContent>
        <TabsContent value="curators" className="mt-4"><CuratorsTab /></TabsContent>
      </Tabs>
    </>
  );
}
