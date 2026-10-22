import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiGet, apiSend } from "./api";

function respond(status: number, body: unknown) {
  return vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } }));
}

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("GET builds the URL with params and returns JSON", async () => {
    const fetchMock = respond(200, { ok: 1 });
    vi.stubGlobal("fetch", fetchMock);
    expect(await apiGet("/api/students", new URLSearchParams("course=2"))).toEqual({ ok: 1 });
    expect(fetchMock.mock.calls[0][0]).toBe("/api/students?course=2");
  });

  it("a 409 becomes ApiError carrying the server detail", async () => {
    vi.stubGlobal("fetch", respond(409, { detail: "Key (tax_id) already exists", constraint: "uq_student_tax_id" }));
    const err = (await apiSend("PATCH", "/api/students/1", { tax_id: "1" }).catch((e) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect([err.status, err.message, err.constraint]).toEqual([409, "Key (tax_id) already exists", "uq_student_tax_id"]);
  });

  it("FastAPI validation errors are flattened into one message", async () => {
    vi.stubGlobal("fetch", respond(422, { detail: [{ loc: ["body", "tax_id"], msg: "String should match pattern" }] }));
    const err = (await apiSend("POST", "/api/students", {}).catch((e) => e)) as ApiError;
    expect(err.message).toBe("tax_id: String should match pattern");
  });
});
