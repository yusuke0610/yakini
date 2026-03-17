import { useState } from "react";

import type { CareerProjectForm } from "../../payloadBuilders";
import type { CareerTechnologyStack, CareerTechnologyStackCategory } from "../../types";
import type { CareerProjectFieldKey } from "../../formTypes";
import {
  blankCareerTechnologyStack,
  blankTeamMember,
  careerTechnologyStackCategories,
  careerTechnologyStackCategoryLabels,
  phaseOptions,
  teamRoleOptions,
} from "../../constants";
import { Combobox } from "./Combobox";
import { MarkdownTextarea } from "./MarkdownTextarea";
import styles from "./ProjectModal.module.css";

type ProjectModalProps = {
  /** 編集対象のプロジェクト（nullの場合は新規追加） */
  project: CareerProjectForm | null;
  /** 保存時のコールバック */
  onSave: (project: CareerProjectForm) => void;
  /** 閉じるコールバック */
  onClose: () => void;
  /** カテゴリごとの技術スタック名称リスト */
  techStackNamesByCategory: Map<string, string[]>;
};

/** プロジェクト情報を初期化する */
function initProject(project: CareerProjectForm | null): CareerProjectForm {
  if (project) {
    return JSON.parse(JSON.stringify(project));
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

export function ProjectModal({
  project,
  onSave,
  onClose,
  techStackNamesByCategory,
}: ProjectModalProps) {
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

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <span>{project ? "プロジェクト編集" : "プロジェクト追加"}</span>
          <div className={styles.headerActions}>
            <button type="button" className="primary" onClick={() => onSave(local)}>
              保存
            </button>
            <button type="button" onClick={onClose}>
              キャンセル
            </button>
          </div>
        </div>

        <div className={styles.body}>
          <label>
            プロジェクト名
            <input
              type="text"
              value={local.name}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="例: エネルギー業界 IoT Web API アプリ新規開発"
            />
          </label>

          <div className={styles.inline}>
            <label>
              開始
              <input
                type="month"
                value={local.start_date}
                onChange={(e) => updateField("start_date", e.target.value)}
              />
            </label>
            <label>
              参画状況
              <select
                value={local.is_current ? "current" : "ended"}
                onChange={(e) => updateField("is_current", e.target.value === "current")}
              >
                <option value="ended">終了</option>
                <option value="current">参画中</option>
              </select>
            </label>
            {!local.is_current && (
              <label>
                終了
                <input
                  type="month"
                  value={local.end_date}
                  onChange={(e) => updateField("end_date", e.target.value)}
                />
              </label>
            )}
          </div>

          <label>
            役割
            <input
              type="text"
              value={local.role}
              onChange={(e) => updateField("role", e.target.value)}
              placeholder="例: アジャイル開発メンバー"
            />
          </label>

          {/* 体制 */}
          <div className={styles.stackSection}>
            <h3>体制</h3>
            <div className={styles.teamLayout}>
              <label className={styles.teamTotal}>
                <span>全体人数</span>
                <div className={styles.inputWithUnit}>
                  <input
                    type="number"
                    value={local.team.total}
                    onChange={(e) => updateTeamTotal(e.target.value)}
                    placeholder="例: 10"
                  />
                  <span className={styles.unit}>名</span>
                </div>
              </label>

              <button
                type="button"
                className={`ghost ${styles.chipAdd}`}
                onClick={addTeamMember}
              >
                + 役割を追加
              </button>

              {local.team.members.map((member, memberIndex) => (
                <div key={`member-${memberIndex}`} className={styles.stackChip}>
                  <select
                    className={styles.chipSelect}
                    value={member.role}
                    onChange={(e) => updateTeamMember(memberIndex, "role", e.target.value)}
                  >
                    <option value="">選択</option>
                    {teamRoleOptions.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                  <div className={styles.inputWithUnit}>
                    <input
                      type="number"
                      value={member.count}
                      onChange={(e) => updateTeamMember(memberIndex, "count", e.target.value)}
                      placeholder="人数"
                      style={{ width: "5em" }}
                    />
                    <span className={styles.unit}>名</span>
                  </div>
                  <button
                    type="button"
                    className={styles.chipRemove}
                    onClick={() => removeTeamMember(memberIndex)}
                    aria-label="役割を削除"
                  >
                    &times;
                  </button>
                </div>
              ))}
            </div>
          </div>

          <label>
            プロジェクト概要
            <input
              type="text"
              value={local.description}
              onChange={(e) => updateField("description", e.target.value)}
            />
          </label>

          <MarkdownTextarea
            label="課題"
            value={local.challenge}
            onChange={(v) => updateField("challenge", v)}
            rows={2}
          />

          <MarkdownTextarea
            label="行動"
            value={local.action}
            onChange={(v) => updateField("action", v)}
            rows={2}
          />

          <MarkdownTextarea
            label="成果"
            value={local.result}
            onChange={(v) => updateField("result", v)}
            rows={2}
          />

          {/* 技術スタック */}
          <div className={styles.stackSection}>
            <h3>技術スタック</h3>
            <div className={styles.stackGrid}>
              {local.technology_stacks.map((stack, stackIndex) => (
                <div key={`stack-${stackIndex}`} className={styles.stackChip}>
                  <select
                    className={styles.chipSelect}
                    value={stack.category}
                    onChange={(e) => updateTechStack(stackIndex, "category", e.target.value)}
                  >
                    {careerTechnologyStackCategories.map((cat) => (
                      <option key={cat} value={cat}>
                        {careerTechnologyStackCategoryLabels[cat]}
                      </option>
                    ))}
                  </select>
                  <Combobox
                    value={stack.name}
                    onChange={(val) => updateTechStack(stackIndex, "name", val)}
                    options={techStackNamesByCategory.get(stack.category) ?? []}
                    placeholder="例: TypeScript"
                    allowCustom
                  />
                  <button
                    type="button"
                    className={styles.chipRemove}
                    onClick={() => removeTechStack(stackIndex)}
                    aria-label="技術スタックを削除"
                  >
                    &times;
                  </button>
                </div>
              ))}
              <button
                type="button"
                className={`ghost ${styles.chipAdd}`}
                onClick={addTechStack}
              >
                + 追加
              </button>
            </div>
          </div>

          {/* 工程 */}
          <div className={styles.stackSection}>
            <h3>工程</h3>
            <div className={styles.phaseList}>
              {phaseOptions.map((phase) => (
                <label
                  key={`phase-${phase}`}
                  className={styles.stackChip}
                  style={{ cursor: "pointer" }}
                >
                  <input
                    type="checkbox"
                    checked={local.phases.includes(phase)}
                    onChange={() => togglePhase(phase)}
                  />
                  {phase}
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
