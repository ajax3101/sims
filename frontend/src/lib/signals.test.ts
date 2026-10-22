import { describe, expect, it } from "vitest";

import { signalsFor } from "./signals";

const base = { status: "active", has_academic_debt: false, financial_debt: "0.00" };

describe("signalsFor", () => {
  it("no signals for a clean active student", () => {
    expect(signalsFor(base)).toEqual([]);
  });

  it("orders academic debt, tuition debt, then status", () => {
    expect(signalsFor({ status: "academic_leave", has_academic_debt: true, financial_debt: "15000.00" }).map((s) => s.kind))
      .toEqual(["academic", "tuition", "academic_leave"]);
  });

  it("labels tuition debt with the amount", () => {
    expect(signalsFor({ ...base, financial_debt: "1250.50" })).toEqual([
      { kind: "tuition", label: "Борг з оплати: 1 250,50 ₴" },
    ]);
  });

  it.each([["expelled", "Відрахований"], ["graduated", "Випускник"]])("status %s", (status, label) => {
    expect(signalsFor({ ...base, status })).toEqual([{ kind: status, label }]);
  });
});
