export const STATUS: Record<string, string> = {
  active: "Навчається", academic_leave: "Академвідпустка", expelled: "Відрахований", graduated: "Випускник",
};
export const FUNDING: Record<string, string> = { budget: "Бюджет", contract: "Контракт", other: "Інше" };
export const LEVEL: Record<string, string> = { bachelor: "Бакалавр", master: "Магістр", phd: "Доктор філософії" };
export const FORM: Record<string, string> = { full_time: "Денна", part_time: "Заочна", dual: "Дуальна" };
export const CONTROL_FORM: Record<string, string> = {
  exam: "Екзамен", credit: "Залік", diff_credit: "Диф. залік", coursework: "Курсова робота",
};
export const NATIONAL: Record<string, string> = {
  excellent: "відмінно", good: "добре", satisfactory: "задовільно", unsatisfactory: "незадовільно",
  passed: "зараховано", failed: "не зараховано",
};
export const GRADE_KIND: Record<string, string> = {
  current: "Поточна", final: "Підсумкова", retake: "Перескладання", commission: "Комісія",
};
export const DEBT_STATUS: Record<string, string> = {
  open: "Відкрита", retake_scheduled: "Призначено перескладання", closed: "Закрита", written_off: "Списана",
};
export const MEMBERSHIP_REASON: Record<string, string> = {
  enrollment: "Зарахування", transfer: "Переведення", reinstatement: "Поновлення", promotion: "Переведення на курс",
};
export const CONTRACT_STATUS: Record<string, string> = { active: "Діє", terminated: "Розірвано", completed: "Виконано" };

export const label = (map: Record<string, string>, value: string | null | undefined) =>
  value ? (map[value] ?? value) : "—";
