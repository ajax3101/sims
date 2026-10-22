import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend, apiUpload } from "@/lib/api";
import { markFresh } from "@/lib/fresh";

import type {
  AcademicYear, Dictionaries, Finance, Group, GroupDiscipline, History, ImportReport, Page, Performance, Staff,
  Student, StudentListItem, UUID,
} from "./types";

const STATIC = { staleTime: 5 * 60_000 };

export const useDictionaries = () =>
  useQuery({ queryKey: ["dictionaries"], queryFn: () => apiGet<Dictionaries>("/api/dictionaries"), ...STATIC });

export const useCurrentYear = () =>
  useQuery({
    queryKey: ["academic-years", "current"],
    queryFn: () => apiGet<AcademicYear>("/api/academic-years/current").catch(() => null),
    ...STATIC,
  });

export const useStudents = (params: URLSearchParams) =>
  useQuery({
    queryKey: ["students", params.toString()],
    queryFn: () => apiGet<Page<StudentListItem>>("/api/students", params),
    placeholderData: keepPreviousData,
  });

export const useStudent = (id: UUID | undefined) =>
  useQuery({ queryKey: ["student", id], queryFn: () => apiGet<Student>(`/api/students/${id}`), enabled: !!id });

export const usePerformance = (id: UUID) =>
  useQuery({ queryKey: ["student", id, "performance"], queryFn: () => apiGet<Performance>(`/api/students/${id}/performance`) });

export const useFinance = (id: UUID) =>
  useQuery({ queryKey: ["student", id, "finance"], queryFn: () => apiGet<Finance>(`/api/students/${id}/finance`) });

export const useHistory = (id: UUID) =>
  useQuery({ queryKey: ["student", id, "history"], queryFn: () => apiGet<History>(`/api/students/${id}/history`) });

export const useGroups = (params: URLSearchParams) =>
  useQuery({
    queryKey: ["groups", params.toString()],
    queryFn: () => apiGet<Page<Group>>("/api/groups", params),
    placeholderData: keepPreviousData,
  });

export const useAllGroups = () =>
  useQuery({
    queryKey: ["groups", "all"],
    queryFn: () => apiGet<Page<Group>>("/api/groups", new URLSearchParams({ size: "200" })),
    ...STATIC,
  });

export const useGroup = (id: UUID | undefined) =>
  useQuery({ queryKey: ["group", id], queryFn: () => apiGet<Group>(`/api/groups/${id}`), enabled: !!id });

export const useCurriculum = (groupId: UUID) =>
  useQuery({ queryKey: ["group", groupId, "disciplines"], queryFn: () => apiGet<GroupDiscipline[]>(`/api/groups/${groupId}/disciplines`) });

export const useCuratorHistory = (groupId: UUID) =>
  useQuery({
    queryKey: ["group", groupId, "curators"],
    queryFn: () => apiGet<{ id: UUID; starts_on: string; ends_on: string | null; staff: Staff }[]>(`/api/groups/${groupId}/curators`),
  });

export const useStaff = (q: string) =>
  useQuery({
    queryKey: ["staff", q],
    queryFn: () => apiGet<Page<Staff>>("/api/staff", new URLSearchParams({ q, size: "50", is_active: "true" })),
    placeholderData: keepPreviousData,
  });

/** A mutation that touches one student: refreshes their card and the register, and marks the record fresh. */
export function useStudentMutation<TBody, TOut = Student>(method: "POST" | "PATCH", path: (body: TBody) => string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TBody) => apiSend<TOut>(method, path(body), body),
    onSuccess: (out) => {
      const id = (out as { id?: UUID }).id;
      if (id) markFresh(id);
      qc.invalidateQueries({ queryKey: ["students"] });
      qc.invalidateQueries({ queryKey: ["student"] });
      qc.invalidateQueries({ queryKey: ["groups"] });
    },
  });
}

export function useSend<TBody, TOut>(method: "POST" | "PATCH", path: string | ((b: TBody) => string), invalidate: unknown[][]) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TBody) => apiSend<TOut>(method, typeof path === "string" ? path : path(body), body),
    onSuccess: () => invalidate.forEach((queryKey) => qc.invalidateQueries({ queryKey })),
  });
}

export function useImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (files: File[]) => apiUpload<ImportReport[]>("/api/imports", files),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      qc.invalidateQueries({ queryKey: ["groups"] });
      qc.invalidateQueries({ queryKey: ["dictionaries"] });
    },
  });
}

export const useYears = () =>
  useQuery({ queryKey: ["academic-years"], queryFn: () => apiGet<AcademicYear[]>("/api/academic-years"), ...STATIC });

export const useMeta = () =>
  useQuery({ queryKey: ["meta"], queryFn: () => apiGet<{ demo: boolean }>("/api/meta"), staleTime: Infinity });

export const useSpecialties = () =>
  useQuery({ queryKey: ["specialties"], queryFn: () => apiGet<import("./types").SpecialtyRow[]>("/api/specialties") });

export const useStaffDirectory = (q: string, active: string) =>
  useQuery({
    queryKey: ["staff", "directory", q, active],
    queryFn: () => {
      const params = new URLSearchParams({ size: "200" });
      if (q) params.set("q", q);
      if (active) params.set("is_active", active);
      return apiGet<Page<Staff>>("/api/staff", params);
    },
    placeholderData: keepPreviousData,
  });
