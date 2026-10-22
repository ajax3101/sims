export type UUID = string;
export type Money = string;

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface Ref {
  id: UUID;
  name: string;
}

export interface Specialty {
  id: UUID;
  classifier: "2015" | "2024";
  code: string;
  name: string;
  successor_id: UUID | null;
}

export interface SpecialtyRow extends Specialty {
  field_code: string | null;
  successor_code: string | null;
  groups_count: number;
  students_count: number;
}

export interface Dictionaries {
  levels: { id: UUID; code: string; nqf_level: number; name: string }[];
  forms: { id: UUID; code: string; name: string }[];
  specialties: Specialty[];
  programs: { id: UUID; specialty_id: UUID; level_id: UUID; name: string; short_code: string | null }[];
  org_units: { id: UUID; kind: string; name: string; short_name: string | null; parent_id: UUID | null }[];
}

export interface AcademicYear {
  id: UUID;
  label: string;
  start_year: number;
  starts_on: string;
  ends_on: string;
  is_current: boolean;
}

export interface Group {
  id: UUID;
  code: string;
  code_norm: string;
  specialty: Specialty;
  program: Ref | null;
  level: string;
  form: string;
  org_unit: Ref;
  admission_year: number;
  entry_course: number;
  is_shortened: boolean;
  cohort_tag: string | null;
  study_start: string | null;
  study_end: string | null;
  status: string;
  course: number | null;
  curator: { id: UUID; full_name: string } | null;
}

export interface StudentListItem {
  id: UUID;
  full_name: string;
  last_name: string;
  first_name: string;
  patronymic: string | null;
  status: string;
  funding: string | null;
  record_book_no: string | null;
  group: { id: UUID; code: string } | null;
  specialty: { code: string; name: string } | null;
  course: number | null;
  has_academic_debt: boolean;
  financial_debt: Money;
}

export interface Student {
  id: UUID;
  full_name: string;
  last_name: string;
  first_name: string;
  patronymic: string | null;
  status: string;
  funding: string | null;
  funding_raw: string | null;
  enrolled_on: string | null;
  tax_id: string | null;
  birth_date: string | null;
  gender: string | null;
  contacts: { phone?: string; email?: string; address?: string };
  record_book_no: string | null;
  student_card_no: string | null;
  group: Group | null;
}

export interface Grade {
  id: UUID;
  kind: string;
  attempt_no: number;
  score: number | null;
  ects: string | null;
  national: string | null;
  graded_on: string;
}

export interface Performance {
  semesters: {
    academic_year: string;
    semester: number;
    disciplines: {
      group_discipline_id: UUID;
      discipline: string;
      control_form: string;
      credits_ects: string | null;
      grades: Grade[];
      final: Grade | null;
      has_debt: boolean;
    }[];
  }[];
  debts: {
    id: UUID;
    discipline: string;
    academic_year: string;
    semester: number;
    status: string;
    opened_on: string;
    retake_deadline: string | null;
    closed_on: string | null;
    note: string | null;
  }[];
}

export interface Contract {
  id: UUID;
  number: string;
  signed_on: string | null;
  starts_on: string;
  ends_on: string | null;
  total_amount: Money;
  currency: string;
  status: string;
  schedule: { id: UUID; due_date: string; amount: Money }[];
  payments: { id: UUID; paid_on: string; amount: Money; method: string | null; external_ref: string | null }[];
  due_total: Money;
  paid_total: Money;
  debt: Money;
}

export interface Finance {
  funding: string | null;
  contracts: Contract[];
  total_debt: Money;
}

export interface History {
  memberships: { group: { id: UUID; code: string }; starts_on: string; ends_on: string | null; reason: string; order_ref: string | null }[];
  status_history: { status: string; changed_on: string; order_no: string | null; note: string | null }[];
  documents: { id: UUID; kind: string; title: string; file_path: string | null; issued_on: string | null }[];
}

export interface Staff {
  id: UUID;
  full_name: string;
  last_name: string;
  first_name: string;
  patronymic: string | null;
  position: string | null;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  academic_degree: string | null;
  org_unit_id: UUID | null;
  curated_groups: { id: UUID; code: string }[];
}

export interface Issue {
  severity: "error" | "warning";
  code: string;
  message: string;
  location: Record<string, number | string>;
}

export interface ImportReport {
  batch_id: UUID | null;
  source_filename: string;
  status: string;
  students_created: number;
  students_updated: number;
  duplicates: number;
  groups_created: number;
  groups_matched: number;
  dictionaries_created: Record<string, number>;
  errors: number;
  warnings: number;
  issues: Issue[];
}

export interface GroupDiscipline {
  id: UUID;
  group_id: UUID;
  discipline_id: UUID;
  discipline: string;
  semester_id: UUID;
  academic_year: string;
  semester: number;
  control_form: string;
  credits_ects: string | null;
  teacher_id: UUID | null;
}
