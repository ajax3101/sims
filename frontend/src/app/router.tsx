import { createBrowserRouter, Navigate } from "react-router";

import { StudentsPage } from "@/features/students/StudentsPage";

import { Shell } from "./Shell";

// The register is the home screen and ships in the main bundle; every other screen loads on first visit.
export const router = createBrowserRouter([
  {
    element: <Shell />,
    children: [
      { index: true, element: <Navigate to="/students" replace /> },
      { path: "students", element: <StudentsPage /> },
      { path: "students/:id", lazy: () => import("@/features/students/StudentCardPage").then((m) => ({ Component: m.StudentCardPage })) },
      { path: "groups", lazy: () => import("@/features/groups/GroupsPage").then((m) => ({ Component: m.GroupsPage })) },
      { path: "groups/:id", lazy: () => import("@/features/groups/GroupPage").then((m) => ({ Component: m.GroupPage })) },
      { path: "import", lazy: () => import("@/features/imports/ImportPage").then((m) => ({ Component: m.ImportPage })) },
      { path: "directories", lazy: () => import("@/features/directories/DirectoriesPage").then((m) => ({ Component: m.DirectoriesPage })) },
      { path: "reports", lazy: () => import("@/features/reports/ReportsPage").then((m) => ({ Component: m.ReportsPage })) },
    ],
  },
]);
