import { useMemo } from "react";

import {
  blankCareerClient,
  blankCareerExperience,
  blankCareerProject,
  blankCareerTechnologyStack,
} from "../../../constants";
import type {
  CareerExperienceFieldKey,
  CareerClientFieldKey,
} from "../../../formTypes";
import type { CareerExperienceForm, CareerProjectForm, CareerFormState } from "../../../payloadBuilders";
import type { TechStackMasterItem } from "../../../types";
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
 * experiences の3階層（experience → client → project）の nested update ハンドラと
 * useProjectModalState を一括で担う。
 * CareerResumeForm 本体から分離し、CRUD・モーダル操作の責務をここに集約する。
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

  /** experience フィールド変更ハンドラ */
  const updateExperienceField = (
    index: number,
    key: CareerExperienceFieldKey,
    value: string | boolean,
  ) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, i) => {
        if (i !== index) return exp;
        if (key === "is_current") {
          const isCurrent = Boolean(value);
          return { ...exp, is_current: isCurrent, end_date: isCurrent ? "" : exp.end_date };
        }
        return { ...exp, [key]: value };
      }),
    }));
  };

  /** client フィールド変更ハンドラ */
  const updateClientField = (
    expIndex: number,
    clientIndex: number,
    key: CareerClientFieldKey,
    value: string,
  ) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          clients: exp.clients.map((c, ci) =>
            ci === clientIndex ? { ...c, [key]: value } : c,
          ),
        };
      }),
    }));
  };

  /** 「取引先なし」フラグ切り替えハンドラ */
  const updateClientHasClient = (expIndex: number, clientIndex: number, value: boolean) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          clients: exp.clients.map((c, ci) =>
            ci === clientIndex ? { ...c, has_client: value, name: value ? c.name : "" } : c,
          ),
        };
      }),
    }));
  };

  /** 取引先追加ハンドラ */
  const addClient = (expIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) =>
        ei === expIndex
          ? { ...exp, clients: [...exp.clients, { ...blankCareerClient }] }
          : exp,
      ),
    }));
  };

  /** 取引先削除ハンドラ */
  const removeClient = (expIndex: number, clientIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          clients:
            exp.clients.length === 1
              ? [{ ...blankCareerClient }]
              : exp.clients.filter((_, ci) => ci !== clientIndex),
        };
      }),
    }));
  };

  /** プロジェクト削除ハンドラ */
  const removeProject = (expIndex: number, clientIndex: number, projIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          clients: exp.clients.map((c, ci) => {
            if (ci !== clientIndex) return c;
            return {
              ...c,
              projects:
                c.projects.length === 1
                  ? [{ ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] }]
                  : c.projects.filter((_, pi) => pi !== projIndex),
            };
          }),
        };
      }),
    }));
  };

  /** 職務経歴追加ハンドラ */
  const addExperience = () => {
    setForm((prev) => ({
      ...prev,
      experiences: [...prev.experiences, { ...blankCareerExperience }],
    }));
  };

  /** 職務経歴削除ハンドラ */
  const removeExperience = (index: number) => {
    setForm((prev) => ({
      ...prev,
      experiences:
        prev.experiences.length === 1
          ? [{ ...blankCareerExperience }]
          : prev.experiences.filter((_, i) => i !== index),
    }));
  };

  /**
   * form の experiences からプロジェクトを取得するコールバック。
   * useProjectModalState に渡す。
   */
  const getProject = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
  ): CareerProjectForm | null => {
    return experiences[expIndex]?.clients[clientIndex]?.projects[projIndex] ?? null;
  };

  /**
   * モーダルで保存されたプロジェクトをフォームに反映するコールバック。
   * useProjectModalState に渡す。
   */
  const onProjectSave = (
    expIndex: number,
    clientIndex: number,
    projIndex: number | null,
    project: CareerProjectForm,
  ) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          clients: exp.clients.map((c, ci) => {
            if (ci !== clientIndex) return c;
            if (projIndex === null) {
              return { ...c, projects: [...c.projects, project] };
            }
            return {
              ...c,
              projects: c.projects.map((p, pi) => (pi === projIndex ? project : p)),
            };
          }),
        };
      }),
    }));
  };

  const {
    modalTarget,
    setModalTarget,
    modalProject,
    handleProjectSave,
    closeModal,
  } = useProjectModalState(getProject, onProjectSave);

  /** プロジェクトのサマリーテキストを生成する */
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
          onUpdateExperienceField={updateExperienceField}
          onUpdateClientField={updateClientField}
          onUpdateClientHasClient={updateClientHasClient}
          onAddClient={addClient}
          onRemoveClient={removeClient}
          onRemoveProject={removeProject}
          onOpenProjectModal={handleOpenProjectModal}
          onRemoveExperience={removeExperience}
          projectSummary={projectSummary}
        />
      ))}

      <button type="button" className="ghost" onClick={addExperience}>
        職務経歴を追加
      </button>
    </section>
  );
}
