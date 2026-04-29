import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FrameworkList } from "./FrameworkList";

describe("FrameworkList", () => {
  it("frameworks が空配列の場合は何も描画しない", () => {
    const { container } = render(<FrameworkList frameworks={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("渡された各 framework 名をチップとして表示する", () => {
    render(<FrameworkList frameworks={["React", "Next.js", "FastAPI"]} />);
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.getByText("Next.js")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
    // aria-label 付きリストが描画されること
    expect(
      screen.getByRole("list", { name: "検出フレームワーク一覧" }),
    ).toBeInTheDocument();
  });

  it("渡された順序が保たれる", () => {
    render(<FrameworkList frameworks={["React", "FastAPI", "Docker"]} />);
    const items = screen.getAllByRole("listitem").map((li) => li.textContent);
    expect(items).toEqual(["React", "FastAPI", "Docker"]);
  });
});
