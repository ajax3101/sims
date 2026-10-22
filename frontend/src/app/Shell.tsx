import { BookMarked, FileSpreadsheet, FolderInput, Layers, Users } from "lucide-react";
import { NavLink, Outlet } from "react-router";

import { useCurrentYear } from "@/api/hooks";
import { DemoMark } from "@/components/world/DemoMark";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/students", label: "Студенти", icon: Users },
  { to: "/groups", label: "Групи", icon: Layers },
  { to: "/import", label: "Імпорт", icon: FolderInput },
  { to: "/reports", label: "Звіти", icon: FileSpreadsheet },
  { to: "/directories", label: "Довідники", icon: BookMarked },
];

export function Shell() {
  const year = useCurrentYear();
  return (
    <div className="grid min-h-dvh grid-cols-[232px_minmax(0,1fr)] max-md:grid-cols-1">
      <aside className="sticky top-0 flex h-dvh flex-col bg-rail text-rail-foreground max-md:static max-md:h-auto">
        <div className="px-5 pt-5 pb-6 max-md:pb-3">
          {/* six index tabs, one per course: the card file's own mark */}
          <div aria-hidden className="mb-2 flex h-2 gap-[3px]">
            {[1, 2, 3, 4, 5, 6].map((c) => <span key={c} className="w-4 rounded-t-[3px]" style={{ background: `var(--course-${c})` }} />)}
          </div>
          <div className="text-[1.0625rem] font-semibold tracking-tight">SIMS</div>
          <div className="text-xs text-rail-muted">Деканат · облік студентів</div>
          <DemoMark tone="rail" className="mt-2 md:hidden" />
        </div>
        <nav aria-label="Розділи" className="flex flex-col gap-0.5 px-2 max-md:grid max-md:grid-cols-5 max-md:gap-1 max-md:pb-2">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-[0.875rem] text-rail-muted transition-colors duration-150",
                  "max-md:flex-col max-md:gap-1 max-md:px-1 max-md:py-1.5 max-md:text-xs",
                  "hover:bg-rail-active/60 hover:text-rail-foreground focus-visible:outline-rail-foreground",
                  isActive && "bg-rail-active font-medium text-rail-foreground",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={cn("size-4 transition-colors duration-150", isActive && "text-sun")} aria-hidden />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto border-t border-white/10 px-5 py-4 text-xs text-rail-muted max-md:hidden">
          Навчальний рік
          <div className="mt-0.5 text-sm font-medium text-rail-foreground tabular">
            {year.data ? year.data.label : year.isLoading ? "…" : "не задано"}
          </div>
          <DemoMark tone="rail" className="mt-3" />
        </div>
      </aside>
      <main className="min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
