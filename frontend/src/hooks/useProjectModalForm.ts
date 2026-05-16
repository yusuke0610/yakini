import { useState } from "react";

import {
  blankCareerTechnologyStack,
  blankTeamMember,
} from "../constants";
import type { CareerProjectFieldKey } from "../formTypes";
import {
  validateDateRange,
  type CareerProjectForm,
} from "../payloadBuilders";
import type { CareerTechnologyStack, CareerTechnologyStackCategory } from "../types";

/**
 * 編集対象が無い（新規追加）場合の初期プロジェクトを生成する。
 * 既存プロジェクトを編集する場合は structuredClone で副作用を切る。
 */
export function initProject(project: CareerProjectForm | null): CareerProjectForm {
  if (project) {
    return structuredClone(project);
  }
  return {
    name: "",
    start_date: "",
    end_date: "",
    is_current: false,
    role: "",
    description: "",
    challenge: "",
    action: "",
    result: "",
    team: { total: "", members: [] },
    technology_stacks: [{ ...blankCareerTechnologyStack }],
    phases: [],
  };
}

/**
 * プロジェクト編集モーダルの state と nested update ハンドラを提供するフック。
 * ProjectModal の責務を JSX に絞るために、データ操作ロジックを切り出している。
 */
export function useProjectModalForm(project: CareerProjectForm | null) {
  const [local, setLocal] = useState<CareerProjectForm>(() => initProject(project));

  const updateField = (key: CareerProjectFieldKey, value: string | boolean) => {
    setLocal((prev) => {
      if (key === "is_current") {
        const isCurrent = Boolean(value);
        return { ...prev, is_current: isCurrent, end_date: isCurrent ? "" : prev.end_date };
      }
      return { ...prev, [key]: value };
    });
  };

  const updateTechStack = (
    stackIndex: number,
    key: keyof CareerTechnologyStack,
    value: string,
  ) => {
    setLocal((prev) => ({
      ...prev,
      technology_stacks: prev.technology_stacks.map((stack, si) => {
        if (si !== stackIndex) return stack;
        if (key === "category") {
          return { ...stack, category: value as CareerTechnologyStackCategory, name: "" };
        }
        return { ...stack, name: value };
      }),
    }));
  };

  const addTechStack = () => {
    setLocal((prev) => ({
      ...prev,
      technology_stacks: [...prev.technology_stacks, { ...blankCareerTechnologyStack }],
    }));
  };

  const removeTechStack = (stackIndex: number) => {
    setLocal((prev) => ({
      ...prev,
      technology_stacks:
        prev.technology_stacks.length === 1
          ? [{ ...blankCareerTechnologyStack }]
          : prev.technology_stacks.filter((_, si) => si !== stackIndex),
    }));
  };

  const updateTeamTotal = (value: string) => {
    setLocal((prev) => ({ ...prev, team: { ...prev.team, total: value } }));
  };

  const addTeamMember = () => {
    setLocal((prev) => ({
      ...prev,
      team: { ...prev.team, members: [...prev.team.members, { ...blankTeamMember }] },
    }));
  };

  const removeTeamMember = (memberIndex: number) => {
    setLocal((prev) => ({
      ...prev,
      team: {
        ...prev.team,
        members: prev.team.members.filter((_, mi) => mi !== memberIndex),
      },
    }));
  };

  const updateTeamMember = (memberIndex: number, key: "role" | "count", value: string) => {
    setLocal((prev) => ({
      ...prev,
      team: {
        ...prev.team,
        members: prev.team.members.map((m, mi) =>
          mi === memberIndex ? { ...m, [key]: value } : m,
        ),
      },
    }));
  };

  const togglePhase = (phase: string) => {
    setLocal((prev) => {
      const phases = prev.phases.includes(phase)
        ? prev.phases.filter((p) => p !== phase)
        : [...prev.phases, phase];
      return { ...prev, phases };
    });
  };

  const dateError = validateDateRange(local.start_date, local.end_date, local.is_current);

  return {
    local,
    dateError,
    updateField,
    updateTechStack,
    addTechStack,
    removeTechStack,
    updateTeamTotal,
    addTeamMember,
    removeTeamMember,
    updateTeamMember,
    togglePhase,
  };
}
