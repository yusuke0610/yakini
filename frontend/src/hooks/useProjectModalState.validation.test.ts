import { describe, it, expect } from "vitest";
import { validateDateRange } from "../payloadBuilders";

/**
 * ProjectModal で使用される日付バリデーション関数のテスト。
 * 開始日 > 終了日 の場合にエラーメッセージを返すことを確認する。
 */
describe("validateDateRange (ProjectModal 日付バリデーション)", () => {
  /** 開始日 > 終了日 の場合にエラーメッセージが返されること */
  it("開始日が終了日より後の場合にエラーメッセージが返される", () => {
    const error = validateDateRange("2024-06", "2024-01", false);
    expect(error).not.toBeNull();
    expect(error).toContain("開始日");
  });

  /** 開始日 === 終了日 の場合はエラーにならないこと */
  it("開始日と終了日が同じ場合はエラーにならない", () => {
    const error = validateDateRange("2024-01", "2024-01", false);
    expect(error).toBeNull();
  });

  /** 開始日 < 終了日 の場合はエラーにならないこと */
  it("開始日が終了日より前の場合はエラーにならない", () => {
    const error = validateDateRange("2024-01", "2024-12", false);
    expect(error).toBeNull();
  });

  /** is_current が true の場合は終了日にかかわらずエラーにならないこと */
  it("is_current が true の場合は終了日が不正でもエラーにならない", () => {
    const error = validateDateRange("2024-06", "2024-01", true);
    expect(error).toBeNull();
  });

  /** 開始日が空の場合はエラーにならないこと */
  it("開始日が空の場合はエラーにならない", () => {
    const error = validateDateRange("", "2024-01", false);
    expect(error).toBeNull();
  });

  /** 終了日が空の場合はエラーにならないこと */
  it("終了日が空の場合はエラーにならない", () => {
    const error = validateDateRange("2024-01", "", false);
    expect(error).toBeNull();
  });
});
