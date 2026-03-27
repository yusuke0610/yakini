import { useState } from "react";

import type { CareerProjectForm } from "../payloadBuilders";

/** プロジェクトモーダルの対象を表す型 */
export type ProjectModalTarget = {
  expIndex: number;
  clientIndex: number;
  /** null の場合は新規追加 */
  projIndex: number | null;
};

/**
 * CareerResumeForm の ProjectModal 状態管理を担うカスタムフック。
 * モーダルの開閉・対象プロジェクトの算出・保存ハンドラを提供する。
 */
export function useProjectModalState(
  getProject: (expIndex: number, clientIndex: number, projIndex: number) => CareerProjectForm | null,
  onSave: (expIndex: number, clientIndex: number, projIndex: number | null, project: CareerProjectForm) => void,
) {
  const [modalTarget, setModalTarget] = useState<ProjectModalTarget | null>(null);

  /**
   * モーダルに渡す現在のプロジェクトデータを取得する。
   * 新規追加の場合は null を返す。
   */
  const modalProject: CareerProjectForm | null = modalTarget
    ? modalTarget.projIndex !== null
      ? getProject(modalTarget.expIndex, modalTarget.clientIndex, modalTarget.projIndex)
      : null
    : null;

  /**
   * モーダルの保存コールバック。
   */
  const handleProjectSave = (project: CareerProjectForm) => {
    if (!modalTarget) return;
    onSave(modalTarget.expIndex, modalTarget.clientIndex, modalTarget.projIndex, project);
    setModalTarget(null);
  };

  /** モーダルを閉じる。 */
  const closeModal = () => setModalTarget(null);

  return {
    modalTarget,
    setModalTarget,
    modalProject,
    handleProjectSave,
    closeModal,
  };
}
