import { describe, it, expect } from "vitest";
import {
  validateEmail,
  validatePassword,
  validateAppointmentStartInFuture,
  parseLocalDateTime,
} from "./formValidation";

describe("formValidation (UI)", () => {
  it("U-01: validateEmail accepts user@example.com", () => {
    expect(validateEmail("user@example.com")).toBeNull();
  });

  it("U-02: validateEmail rejects string without @", () => {
    expect(validateEmail("not-an-email")).toMatch(/некорректн/i);
  });

  it("U-03: validatePassword rejects password shorter than 8", () => {
    expect(validatePassword("short")).toMatch(/8/);
  });

  it("U-04: validateAppointmentStartInFuture rejects past date for new booking", () => {
    const past = new Date();
    past.setDate(past.getDate() - 7);
    const date = past.toISOString().slice(0, 10);
    expect(validateAppointmentStartInFuture(date, "10:00", { isEdit: false })).toMatch(/будущ/i);
  });

  it("parseLocalDateTime parses ISO-like local strings", () => {
    const dt = parseLocalDateTime("2026-12-01", "14:30");
    expect(dt).not.toBeNull();
    expect(dt!.getFullYear()).toBe(2026);
    expect(dt!.getMonth()).toBe(11);
    expect(dt!.getHours()).toBe(14);
  });
});
