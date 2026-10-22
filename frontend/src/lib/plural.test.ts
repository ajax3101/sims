import { describe, expect, it } from "vitest";

import { plural } from "./plural";

const RECORDS = ["запис", "записи", "записів"] as const;

describe("plural (Ukrainian)", () => {
  it.each([
    [0, "записів"], [1, "запис"], [2, "записи"], [4, "записи"], [5, "записів"], [11, "записів"],
    [12, "записів"], [14, "записів"], [21, "запис"], [22, "записи"], [25, "записів"], [101, "запис"], [111, "записів"],
    [252, "записи"],
  ])("%i → %s", (n, want) => {
    expect(plural(n, RECORDS)).toBe(want);
  });
});
