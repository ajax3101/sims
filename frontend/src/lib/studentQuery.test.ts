import { describe, expect, it } from "vitest";

import { nextSort, parseStudentQuery, toApiParams, withFilter } from "./studentQuery";

describe("parseStudentQuery", () => {
  it("applies defaults", () => {
    expect(parseStudentQuery(new URLSearchParams())).toEqual({ page: 1, size: 50, sort: "name", filters: {} });
  });

  it("reads filters, booleans and paging from the URL", () => {
    const q = parseStudentQuery(new URLSearchParams("course=2&has_academic_debt=true&q=бад&page=3&size=25&sort=-course"));
    expect(q).toEqual({ page: 3, size: 25, sort: "-course", filters: { course: "2", has_academic_debt: "true", q: "бад" } });
  });

  it("drops unknown keys and invalid paging", () => {
    expect(parseStudentQuery(new URLSearchParams("evil=1&page=-4&size=9999&sort=password"))).toEqual({
      page: 1, size: 50, sort: "name", filters: {},
    });
  });
});

describe("toApiParams", () => {
  it("serialises only non-empty values", () => {
    const params = toApiParams({ page: 2, size: 50, sort: "-name", filters: { course: "2", q: "  ", funding: "" } });
    expect(params.toString()).toBe("page=2&size=50&sort=-name&course=2");
  });
});

describe("withFilter", () => {
  it("sets a filter and resets to the first page", () => {
    const base = { page: 4, size: 50, sort: "name", filters: { course: "1" } };
    expect(withFilter(base, "funding", "contract")).toEqual({ ...base, page: 1, filters: { course: "1", funding: "contract" } });
  });

  it("removes a filter when the value is empty", () => {
    const base = { page: 1, size: 50, sort: "name", filters: { course: "1" } };
    expect(withFilter(base, "course", "").filters).toEqual({});
  });
});

describe("nextSort", () => {
  it.each([
    ["name", "name", "-name"],
    ["-name", "name", "name"],
    ["name", "course", "course"],
    ["-course", "group", "group"],
  ])("from %s clicking %s gives %s", (current, column, want) => {
    expect(nextSort(current, column)).toBe(want);
  });
});
