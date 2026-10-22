import { describe, expect, it } from "vitest";

import { instalmentStates } from "./instalments";

const S = [
  { due_date: "2025-09-15", amount: "16000.00" },
  { due_date: "2026-02-15", amount: "16000.00" },
  { due_date: "2026-09-15", amount: "16000.00" },
  { due_date: "2027-02-15", amount: "16000.00" },
];
const TODAY = "2026-10-19";

describe("instalmentStates (payments settle the oldest instalment first)", () => {
  it("fully paid up to today", () => {
    expect(instalmentStates(S, "48000.00", TODAY)).toEqual(["paid", "paid", "paid", "upcoming"]);
  });

  it("half paid: one settled, one partly, the rest overdue or upcoming", () => {
    expect(instalmentStates(S, "24000.00", TODAY)).toEqual(["paid", "partial", "overdue", "upcoming"]);
  });

  it("nothing paid", () => {
    expect(instalmentStates(S, "0", TODAY)).toEqual(["overdue", "overdue", "overdue", "upcoming"]);
  });

  it("prepayment covers a future instalment", () => {
    expect(instalmentStates(S, "64000.00", TODAY)).toEqual(["paid", "paid", "paid", "paid"]);
  });

  it("order of the input does not matter", () => {
    expect(instalmentStates([S[3], S[0]], "16000.00", TODAY)).toEqual(["upcoming", "paid"]);
  });
});
