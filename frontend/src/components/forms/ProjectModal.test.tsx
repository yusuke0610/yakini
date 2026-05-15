import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectModal } from "./ProjectModal";
import type { CareerProjectForm } from "../../payloadBuilders";

const invalidDateProject: CareerProjectForm = {
  name: "テスト",
  start_date: "2024-12",
  end_date: "2024-01",
  is_current: false,
  role: "エンジニア",
  description: "",
  challenge: "",
  action: "",
  result: "",
  team: { total: "", members: [] },
  technology_stacks: [],
  phases: [],
};

describe("ProjectModal", () => {
  /** 開始日 > 終了日 のとき保存ボタンが disabled になること */
  it("開始日が終了日より後の場合に保存ボタンが disabled になる", () => {
    render(
      <ProjectModal
        project={invalidDateProject}
        onSave={vi.fn()}
        onClose={vi.fn()}
        techStackNamesByCategory={new Map()}
      />,
    );
    expect(screen.getByRole("button", { name: "保存" })).toBeDisabled();
  });
});
