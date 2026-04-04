import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectModal } from "./ProjectModal";
import type { CareerProjectForm } from "../../payloadBuilders";

/** テスト用のダミープロジェクトデータ（正常な日付） */
const validProject: CareerProjectForm = {
  name: "テストプロジェクト",
  start_date: "2024-01",
  end_date: "2024-12",
  is_current: false,
  role: "エンジニア",
  description: "プロジェクト概要",
  challenge: "課題",
  action: "対応",
  result: "成果",
  team: { total: "5", members: [] },
  technology_stacks: [],
  phases: [],
};

/** テスト用のダミープロジェクトデータ（不正な日付: 開始日 > 終了日） */
const invalidDateProject: CareerProjectForm = {
  ...validProject,
  start_date: "2024-12",
  end_date: "2024-01",
};

describe("ProjectModal 日付バリデーション", () => {
  /** 開始日 > 終了日 の場合にエラーメッセージが表示されること */
  it("開始日が終了日より後の場合にエラーメッセージが表示される", () => {
    const onSave = vi.fn();
    const onClose = vi.fn();

    render(
      <ProjectModal
        project={invalidDateProject}
        onSave={onSave}
        onClose={onClose}
        techStackNamesByCategory={new Map()}
      />,
    );

    expect(screen.getByText(/開始日は終了日より前に設定してください/)).toBeInTheDocument();
  });

  /** 開始日 > 終了日 の場合に保存ボタンが disabled になること */
  it("開始日が終了日より後の場合に保存ボタンが disabled になる", () => {
    const onSave = vi.fn();
    const onClose = vi.fn();

    render(
      <ProjectModal
        project={invalidDateProject}
        onSave={onSave}
        onClose={onClose}
        techStackNamesByCategory={new Map()}
      />,
    );

    const saveButton = screen.getByRole("button", { name: "保存" });
    expect(saveButton).toBeDisabled();
  });

  /** 正常な日付の場合に保存ボタンが有効であること */
  it("正常な日付の場合に保存ボタンが有効である", () => {
    const onSave = vi.fn();
    const onClose = vi.fn();

    render(
      <ProjectModal
        project={validProject}
        onSave={onSave}
        onClose={onClose}
        techStackNamesByCategory={new Map()}
      />,
    );

    const saveButton = screen.getByRole("button", { name: "保存" });
    expect(saveButton).not.toBeDisabled();
  });

  /** 正常な日付の場合にエラーメッセージが表示されないこと */
  it("正常な日付の場合にエラーメッセージが表示されない", () => {
    const onSave = vi.fn();
    const onClose = vi.fn();

    render(
      <ProjectModal
        project={validProject}
        onSave={onSave}
        onClose={onClose}
        techStackNamesByCategory={new Map()}
      />,
    );

    expect(
      screen.queryByText(/開始日は終了日より前に設定してください/),
    ).not.toBeInTheDocument();
  });
});
