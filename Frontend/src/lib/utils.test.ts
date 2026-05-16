import { describe, it, expect } from "vitest";
import { cn } from "./utils";

describe("utils.cn (UI)", () => {
  it("U-05: tailwind-merge resolves conflicting padding classes", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });
});
