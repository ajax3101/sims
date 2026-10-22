/** Index-tab colour per course (1–6); classes are spelled out so Tailwind sees them. */
const COURSE_BG: Record<number, string> = {
  1: "bg-course-1", 2: "bg-course-2", 3: "bg-course-3", 4: "bg-course-4", 5: "bg-course-5", 6: "bg-course-6",
};

export function courseClass(course: number | null | undefined): string {
  return (course && COURSE_BG[course]) || "bg-muted";
}
