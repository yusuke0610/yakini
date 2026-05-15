import { useMemo } from "react";

import type { CareerExperienceForm, CareerFormState, CareerProjectForm } from "../../../payloadBuilders";
import type { TechStackMasterItem } from "../../../types";
import { useCareerExperienceMutators } from "../../../hooks/useCareerExperienceMutators";
import { useProjectModalState } from "../../../hooks/useProjectModalState";
import shared from "../../../styles/shared.module.css";
import { CareerExperienceEditor } from "../CareerFormEditors/CareerExperienceEditor";
import { ProjectModal } from "../ProjectModal";

/** CareerExperienceSection のプロパティ型 */
type CareerExperienceSectionProps = {
  /** 職務経歴データの配列 */
  experiences: CareerExperienceForm[];
  /** フォーム状態更新ディスパッチャ */
  setForm: React.Dispatch<React.SetStateAction<CareerFormState>>;
  /** 技術スタックのマスタデータ */
  techStackOptions: TechStackMasterItem[];
};

/**
 * 職務経歴書の職務経歴セクション。
 * 更新ロジックは useCareerExperienceMutators に委譲し、
 * モーダル管理は useProjectModalState に委譲する。
 */
export function CareerExperienceSection({
  experiences,
  setForm,
  techStackOptions,
}: CareerExperienceSectionProps) {
  /** カテゴリごとの技術スタック名称マップを生成する */
  const techStackNamesByCategory = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const item of techStackOptions) {
      const list = map.get(item.category) ?? [];
      list.push(item.name);
      map.set(item.category, list);
    }
    return map;
  }, [techStackOptions]);

  const mutators = useCareerExperienceMutators(experiences, setForm);

  const {
    modalTarget,
    setModalTarget,
    modalProject,
    handleProjectSave,
    closeModal,
  } = useProjectModalState(mutators.getProject, mutators.onProjectSave);

  /** プロジェクトの期間サマリーテキストを生成する */
  const projectSummary = (proj: CareerProjectForm) => {
    const period = [proj.start_date, proj.is_current ? "現在" : proj.end_date]
      .filter(Boolean)
      .join(" 〜 ");
    return period || "";
  };

  /** モーダルを開くハンドラ */
  const handleOpenProjectModal = (
    expIndex: number,
    clientIndex: number,
    projIndex: number | null,
  ) => {
    setModalTarget({ expIndex, clientIndex, projIndex });
  };

  return (
    <section className={shared.section}>
      {modalTarget && (
        <ProjectModal
          project={modalProject}
          onSave={handleProjectSave}
          onClose={closeModal}
          techStackNamesByCategory={techStackNamesByCategory}
        />
      )}

      <h2>職務経歴</h2>
      {experiences.map((exp, expIndex) => (
        <CareerExperienceEditor
          key={`exp-${expIndex}`}
          exp={exp}
          expIndex={expIndex}
          onUpdateExperienceField={mutators.updateExperienceField}
          onUpdateClientField={mutators.updateClientField}
          onUpdateClientHasClient={mutators.updateClientHasClient}
          onAddClient={mutators.addClient}
          onRemoveClient={mutators.removeClient}
          onRemoveProject={mutators.removeProject}
          onOpenProjectModal={handleOpenProjectModal}
          onRemoveExperience={mutators.removeExperience}
          projectSummary={projectSummary}
        />
      ))}

      <button type="button" className="ghost" onClick={mutators.addExperience}>
        職務経歴を追加
      </button>
    </section>
  );
}
