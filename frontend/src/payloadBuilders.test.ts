import { describe, it, expect } from "vitest";
import { validateDateRange } from "./payloadBuilders";

describe("validateDateRange", () => {
  it("開始日が終了日より後の場合にエラーメッセージが返される", () => {
    const error = validateDateRange("2024-06", "2024-01", false);
    expect(error).not.toBeNull();
    expect(error).toContain("開始日");
  });

  it("開始日と終了日が同じ場合はエラーにならない", () => {
    expect(validateDateRange("2024-01", "2024-01", false)).toBeNull();
  });

  it("開始日が終了日より前の場合はエラーにならない", () => {
    expect(validateDateRange("2024-01", "2024-12", false)).toBeNull();
  });

  it("is_current が true の場合は終了日が不正でもエラーにならない", () => {
    expect(validateDateRange("2024-06", "2024-01", true)).toBeNull();
  });

  it("開始日または終了日が空の場合はエラーにならない", () => {
    expect(validateDateRange("", "2024-01", false)).toBeNull();
    expect(validateDateRange("2024-01", "", false)).toBeNull();
  });
});
