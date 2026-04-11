import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useProjectModalState } from "./useProjectModalState";
import type { CareerProjectForm } from "../payloadBuilders";

/** テスト用のダミープロジェクトデータ */
const dummyProject: CareerProjectForm = {
  name: "テストプロジェクト",
  start_date: "2024-01",
  end_date: "2024-12",
  is_current: false,
  role: "エンジニア",
  description: "説明",
  challenge: "課題",
  action: "対応",
  result: "結果",
  team: { total: "5", members: [] },
  technology_stacks: [],
  phases: [],
};

describe("useProjectModalState", () => {
  /** 初期状態では modalTarget が null であること */
  it("初期状態では modalTarget が null", () => {
    const getProject = vi.fn();
    const onSave = vi.fn();
    const { result } = renderHook(() => useProjectModalState(getProject, onSave));

    expect(result.current.modalTarget).toBeNull();
  });

  /** setModalTarget を呼ぶと modalTarget が更新されること */
  it("setModalTarget を呼ぶと modalTarget が更新される", () => {
    const getProject = vi.fn();
    const onSave = vi.fn();
    const { result } = renderHook(() => useProjectModalState(getProject, onSave));

    act(() => {
      result.current.setModalTarget({ expIndex: 0, clientIndex: 1, projIndex: 2 });
    });

    expect(result.current.modalTarget).toEqual({ expIndex: 0, clientIndex: 1, projIndex: 2 });
  });

  /** closeModal を呼ぶと modalTarget が null に戻ること */
  it("closeModal を呼ぶと modalTarget が null に戻る", () => {
    const getProject = vi.fn();
    const onSave = vi.fn();
    const { result } = renderHook(() => useProjectModalState(getProject, onSave));

    act(() => {
      result.current.setModalTarget({ expIndex: 0, clientIndex: 0, projIndex: 0 });
    });

    expect(result.current.modalTarget).not.toBeNull();

    act(() => {
      result.current.closeModal();
    });

    expect(result.current.modalTarget).toBeNull();
  });

  /** handleProjectSave を呼ぶと onSave が実行され、modalTarget が null になること */
  it("handleProjectSave を呼ぶと onSave が呼ばれ closeModal が実行される", () => {
    const getProject = vi.fn().mockReturnValue(dummyProject);
    const onSave = vi.fn();
    const { result } = renderHook(() => useProjectModalState(getProject, onSave));

    act(() => {
      result.current.setModalTarget({ expIndex: 1, clientIndex: 2, projIndex: 3 });
    });

    act(() => {
      result.current.handleProjectSave(dummyProject);
    });

    expect(onSave).toHaveBeenCalledWith(1, 2, 3, dummyProject);
    expect(result.current.modalTarget).toBeNull();
  });

  /** modalTarget が null のときに handleProjectSave を呼んでも onSave が実行されないこと */
  it("modalTarget が null のとき handleProjectSave を呼んでも onSave が呼ばれない", () => {
    const getProject = vi.fn();
    const onSave = vi.fn();
    const { result } = renderHook(() => useProjectModalState(getProject, onSave));

    act(() => {
      result.current.handleProjectSave(dummyProject);
    });

    expect(onSave).not.toHaveBeenCalled();
  });

  /** projIndex が null の場合（新規追加）、modalProject が null であること */
  it("projIndex が null のとき modalProject が null になる", () => {
    const getProject = vi.fn().mockReturnValue(dummyProject);
    const onSave = vi.fn();
    const { result } = renderHook(() => useProjectModalState(getProject, onSave));

    act(() => {
      result.current.setModalTarget({ expIndex: 0, clientIndex: 0, projIndex: null });
    });

    expect(result.current.modalProject).toBeNull();
    // 新規追加時は getProject を呼ばない
    expect(getProject).not.toHaveBeenCalled();
  });
});
