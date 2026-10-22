import { describe, expect, it } from "vitest";

import { formatDate, formatMoney } from "./format";

describe("formatMoney", () => {
  it.each([
    ["10000.00", "10 000,00 ₴"],
    ["0.00", "0,00 ₴"],
    ["1234567.5", "1 234 567,50 ₴"],
    [null, "—"],
  ])("%s → %s", (value, want) => {
    expect(formatMoney(value)).toBe(want);
  });
});

describe("formatDate", () => {
  it.each([
    ["2026-01-25", "25.01.2026"],
    [null, "—"],
  ])("%s → %s", (value, want) => {
    expect(formatDate(value)).toBe(want);
  });
});

describe("formatDebt", () => {
  it.each([
    ["0.00", "—"],
    [null, "—"],
    ["1250.50", "1 250,50 ₴"],
  ])("%s → %s", async (value, want) => {
    const { formatDebt } = await import("./format");
    expect(formatDebt(value)).toBe(want);
  });
});
