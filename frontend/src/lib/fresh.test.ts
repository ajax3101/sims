import { beforeEach, describe, expect, it } from "vitest";

import { clearFresh, isFresh, markFresh } from "./fresh";

describe("fresh marks", () => {
  beforeEach(() => sessionStorage.clear());

  it("a record marked fresh stays fresh until opened", () => {
    markFresh("a");
    expect(isFresh("a")).toBe(true);
    clearFresh("a");
    expect(isFresh("a")).toBe(false);
  });

  it("survives a reload within the session", () => {
    markFresh("b");
    expect(JSON.parse(sessionStorage.getItem("sims:fresh") ?? "[]")).toEqual(["b"]);
  });

  it("broken storage never throws", () => {
    sessionStorage.setItem("sims:fresh", "{not json");
    expect(isFresh("x")).toBe(false);
    expect(() => markFresh("x")).not.toThrow();
  });
});
