import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createCareerResume,
  downloadCareerResumeMarkdown,
  downloadCareerResumePdf,
  getCareerResumePdfBlobUrl,
  getLatestBasicInfo,
  getLatestCareerResume,
  updateCareerResume,
} from "../../api";
import { buildCareerPayload } from "../../payloadBuilders";
import type { CareerFormState, CareerProjectForm } from "../../payloadBuilders";
import type { CareerTechnologyStack, CareerTechnologyStackCategory } from "../../types";
import {
  blankCareerClient,
  blankCareerExperience,
  blankCareerProject,
  blankCareerTechnologyStack,
  blankTeamMember,
  careerTechnologyStackCategories,
  careerTechnologyStackCategoryLabels,
  phaseOptions,
  teamRoleOptions,
} from "../../constants";
import type {
  CareerTextFieldKey,
  CareerExperienceFieldKey,
  CareerClientFieldKey,
  CareerProjectFieldKey,
} from "../../formTypes";
import { useTechnologyStacks } from "../../hooks/useMasterData";
import { usePdfActions } from "../../hooks/usePdfActions";
import shared from "../../styles/shared.module.css";
import { Combobox } from "./Combobox";
import { MarkdownTextarea } from "./MarkdownTextarea";
import { PdfPreviewModal } from "./PdfPreviewModal";
import styles from "./CareerResumeForm.module.css";

export function CareerResumeForm() {
  const [form, setForm] = useState<CareerFormState>({
    career_summary: "",
    self_pr: "",
    experiences: [{ ...blankCareerExperience }],
  });
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { items: techStackOptions } = useTechnologyStacks();
  /** カテゴリごとの名称リストを生成する */
  const techStackNamesByCategory = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const item of techStackOptions) {
      const list = map.get(item.category) ?? [];
      list.push(item.name);
      map.set(item.category, list);
    }
    return map;
  }, [techStackOptions]);

  const { downloading, previewUrl, closePreview, onDownloadPdf, onDownloadMarkdown, onPreviewPdf } =
    usePdfActions({
      downloadPdf: downloadCareerResumePdf,
      downloadMarkdown: downloadCareerResumeMarkdown,
      getPdfBlobUrl: getCareerResumePdfBlobUrl,
    });

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const latest = await getLatestCareerResume();
        if (!active) return;
        setResumeId(latest.id);
        setForm({
          career_summary: latest.career_summary,
          self_pr: latest.self_pr,
          experiences:
            latest.experiences.length > 0
              ? latest.experiences.map((exp) => {
                  const raw = exp as Record<string, unknown>;
                  /* 後方互換: 旧形式（projects直下）を clients にラップ */
                  const clients = (raw.clients as typeof exp.clients) ??
                    (raw.projects
                      ? [{ name: "", projects: raw.projects as typeof exp.clients[0]["projects"] }]
                      : []);
                  return {
                    ...exp,
                    end_date: exp.end_date ?? "",
                    clients:
                      clients.length > 0
                        ? clients.map((c) => ({
                            ...c,
                            projects:
                              c.projects.length > 0
                                ? (c.projects as Record<string, unknown>[]).map((p) => {
                                    /* 後方互換: 旧 scale → team, phases 未定義時の補完 */
                                    const patched = { ...p };
                                    if (!patched.team && patched.scale !== undefined) {
                                      patched.team = {
                                        total: String(patched.scale || ""),
                                        members: [],
                                      };
                                    }
                                    if (!patched.team) {
                                      patched.team = { total: "", members: [] };
                                    }
                                    if (!patched.phases) {
                                      patched.phases = [];
                                    }
                                    return patched as unknown as CareerProjectForm;
                                  })
                                : [{ ...blankCareerProject }],
                          }))
                        : [{ ...blankCareerClient }],
                  };
                })
              : [{ ...blankCareerExperience }],
        });
      } catch {
        if (!active) return;
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  const saveButtonText = useMemo(() => {
    if (saving) {
      return "保存中...";
    }
    return resumeId ? "更新する" : "保存する";
  }, [resumeId, saving]);

  const onChangeField = (key: CareerTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

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

  const updateProjectField = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
    key: CareerProjectFieldKey,
    value: string | boolean,
  ) => {
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
              projects: c.projects.map((proj, pi) => {
                if (pi !== projIndex) return proj;
                if (key === "is_current") {
                  const isCurrent = Boolean(value);
                  return { ...proj, is_current: isCurrent, end_date: isCurrent ? "" : proj.end_date };
                }
                return { ...proj, [key]: value };
              }),
            };
          }),
        };
      }),
    }));
  };

  const updateTechnologyStackField = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
    stackIndex: number,
    key: keyof CareerTechnologyStack,
    value: string,
  ) => {
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
              projects: c.projects.map((proj, pi) => {
                if (pi !== projIndex) return proj;
                return {
                  ...proj,
                  technology_stacks: proj.technology_stacks.map((stack, si) => {
                    if (si !== stackIndex) return stack;
                    if (key === "category") {
                      return { ...stack, category: value as CareerTechnologyStackCategory, name: "" };
                    }
                    return { ...stack, name: value };
                  }),
                };
              }),
            };
          }),
        };
      }),
    }));
  };

  const addTechnologyStack = (expIndex: number, clientIndex: number, projIndex: number) => {
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
              projects: c.projects.map((proj, pi) =>
                pi === projIndex
                  ? {
                      ...proj,
                      technology_stacks: [...proj.technology_stacks, { ...blankCareerTechnologyStack }],
                    }
                  : proj,
              ),
            };
          }),
        };
      }),
    }));
  };

  const removeTechnologyStack = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
    stackIndex: number,
  ) => {
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
              projects: c.projects.map((proj, pi) => {
                if (pi !== projIndex) return proj;
                return {
                  ...proj,
                  technology_stacks:
                    proj.technology_stacks.length === 1
                      ? [{ ...blankCareerTechnologyStack }]
                      : proj.technology_stacks.filter((_, si) => si !== stackIndex),
                };
              }),
            };
          }),
        };
      }),
    }));
  };

  const updateTeamTotal = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
    value: string,
  ) => {
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
              projects: c.projects.map((proj, pi) =>
                pi === projIndex ? { ...proj, team: { ...proj.team, total: value } } : proj,
              ),
            };
          }),
        };
      }),
    }));
  };

  const addTeamMember = (expIndex: number, clientIndex: number, projIndex: number) => {
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
              projects: c.projects.map((proj, pi) =>
                pi === projIndex
                  ? { ...proj, team: { ...proj.team, members: [...proj.team.members, { ...blankTeamMember }] } }
                  : proj,
              ),
            };
          }),
        };
      }),
    }));
  };

  const removeTeamMember = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
    memberIndex: number,
  ) => {
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
              projects: c.projects.map((proj, pi) => {
                if (pi !== projIndex) return proj;
                return {
                  ...proj,
                  team: {
                    ...proj.team,
                    members: proj.team.members.filter((_, mi) => mi !== memberIndex),
                  },
                };
              }),
            };
          }),
        };
      }),
    }));
  };

  const updateTeamMember = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
    memberIndex: number,
    key: "role" | "count",
    value: string,
  ) => {
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
              projects: c.projects.map((proj, pi) => {
                if (pi !== projIndex) return proj;
                return {
                  ...proj,
                  team: {
                    ...proj.team,
                    members: proj.team.members.map((m, mi) =>
                      mi === memberIndex ? { ...m, [key]: value } : m,
                    ),
                  },
                };
              }),
            };
          }),
        };
      }),
    }));
  };

  const addProject = (expIndex: number, clientIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          clients: exp.clients.map((c, ci) =>
            ci === clientIndex
              ? {
                  ...c,
                  projects: [
                    ...c.projects,
                    { ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] },
                  ],
                }
              : c,
          ),
        };
      }),
    }));
  };

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

  const togglePhase = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
    phase: string,
  ) => {
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
              projects: c.projects.map((proj, pi) => {
                if (pi !== projIndex) return proj;
                const phases = proj.phases.includes(phase)
                  ? proj.phases.filter((p) => p !== phase)
                  : [...proj.phases, phase];
                return { ...proj, phases };
              }),
            };
          }),
        };
      }),
    }));
  };

  const addExperience = () => {
    setForm((prev) => ({
      ...prev,
      experiences: [...prev.experiences, { ...blankCareerExperience }],
    }));
  };

  const removeExperience = (index: number) => {
    setForm((prev) => ({
      ...prev,
      experiences:
        prev.experiences.length === 1
          ? [{ ...blankCareerExperience }]
          : prev.experiences.filter((_, i) => i !== index),
    }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      try {
        const basicInfo = await getLatestBasicInfo();
        if (!basicInfo.full_name || !basicInfo.record_date) {
          setError("基本情報の氏名と記載日を先に登録してください。");
          setSaving(false);
          return;
        }
      } catch {
        setError("基本情報の氏名と記載日を先に登録してください。");
        setSaving(false);
        return;
      }

      const payload = buildCareerPayload(form);
      const saved = resumeId
        ? await updateCareerResume(resumeId, payload)
        : await createCareerResume(payload);

      setResumeId(saved.id);
      setSuccess("職務経歴書を保存しました。PDF出力できます。");
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "保存中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      {previewUrl && <PdfPreviewModal previewUrl={previewUrl} onClose={closePreview} />}
      <form onSubmit={onSubmit}>
        <div className={shared.pageHeader}>
          <h1>職務経歴書</h1>
          <div className={shared.pageHeaderActions}>
            <button type="submit" className="primary" disabled={saving}>
              {saveButtonText}
            </button>
            <button
              type="button"
              onClick={() => resumeId && onPreviewPdf(resumeId, setError)}
              disabled={!resumeId}
            >
              プレビュー
            </button>
            <button
              type="button"
              onClick={() =>
                resumeId &&
                onDownloadPdf(resumeId, setError, setSuccess, "職務経歴書PDFをダウンロードしました。")
              }
              disabled={!resumeId || downloading}
            >
              {downloading ? "ダウンロード中..." : "PDF出力"}
            </button>
            <button
              type="button"
              onClick={() => resumeId && onDownloadMarkdown(resumeId, setError)}
              disabled={!resumeId}
            >
              Markdown出力
            </button>
          </div>
        </div>

        <div className={shared.pageBody}>
          <div className={shared.form}>
            {error && <p className={shared.error}>{error}</p>}
            {success && <p className={shared.success}>{success}</p>}

            <section className={shared.section}>
              <MarkdownTextarea
                label="職務要約"
                value={form.career_summary}
                onChange={(v) => onChangeField("career_summary", v)}
                rows={4}
                required
              />
              <MarkdownTextarea
                label="自己PR"
                value={form.self_pr}
                onChange={(v) => onChangeField("self_pr", v)}
                rows={4}
                required
              />
            </section>

        <section className={shared.section}>
          <h2>職務経歴</h2>
          {form.experiences.map((exp, expIndex) => (
            <div key={`exp-${expIndex}`} className={shared.entry}>
              <div className={shared.inline}>
                <label>
                  会社名
                  <input
                    type="text"
                    value={exp.company}
                    onChange={(e) => updateExperienceField(expIndex, "company", e.target.value)}
                  />
                </label>
                <label>
                  事業内容
                  <input
                    type="text"
                    value={exp.business_description}
                    onChange={(e) =>
                      updateExperienceField(expIndex, "business_description", e.target.value)
                    }
                    placeholder="例: SES事業、受託開発"
                  />
                </label>
              </div>

              <div className={shared.inline}>
                <label>
                  開始
                  <input
                    type="month"
                    value={exp.start_date}
                    onChange={(e) => updateExperienceField(expIndex, "start_date", e.target.value)}
                  />
                </label>
                <label>
                  在職の有無
                  <select
                    value={exp.is_current ? "current" : "ended"}
                    onChange={(e) =>
                      updateExperienceField(expIndex, "is_current", e.target.value === "current")
                    }
                  >
                    <option value="ended">離職</option>
                    <option value="current">在職</option>
                  </select>
                </label>
                {!exp.is_current && (
                  <label>
                    離職年月
                    <input
                      type="month"
                      value={exp.end_date}
                      onChange={(e) => updateExperienceField(expIndex, "end_date", e.target.value)}
                    />
                  </label>
                )}
              </div>

              <div className={shared.inline}>
                <label>
                  従業員数
                  <div className={styles.inputWithUnit}>
                    <input
                      type="number"
                      value={exp.employee_count}
                      onChange={(e) =>
                        updateExperienceField(expIndex, "employee_count", e.target.value)
                      }
                      placeholder="例: 300"
                    />
                    <span className={styles.unit}>名</span>
                  </div>
                </label>
                <label>
                  資本金
                  <div className={styles.inputWithUnit}>
                    <input
                      type="number"
                      value={exp.capital}
                      onChange={(e) => updateExperienceField(expIndex, "capital", e.target.value)}
                      placeholder="例: 5"
                    />
                    <span className={styles.unit}>千万円</span>
                  </div>
                </label>
              </div>

              {/* Clients (ユーザ) */}
              <div className={styles.stackSection}>
                <h3>取引先（常駐先）</h3>
                {exp.clients.map((client, clientIndex) => (
                  <div key={`client-${expIndex}-${clientIndex}`} className={shared.entry}>
                    <label>
                      取引先名（呼称）
                      <input
                        type="text"
                        value={client.name}
                        onChange={(e) =>
                          updateClientField(expIndex, clientIndex, "name", e.target.value)
                        }
                        placeholder="例: 〇〇社（略称）"
                      />
                    </label>

                    {/* Projects */}
                    <div className={styles.stackSection}>
                      <h3>プロジェクト</h3>
                      {client.projects.map((proj, projIndex) => (
                        <div key={`proj-${expIndex}-${clientIndex}-${projIndex}`} className={shared.entry}>
                          <label>
                            プロジェクト名
                            <input
                              type="text"
                              value={proj.name}
                              onChange={(e) =>
                                updateProjectField(expIndex, clientIndex, projIndex, "name", e.target.value)
                              }
                              placeholder="例: エネルギー業界 IoT Web API アプリ新規開発"
                            />
                          </label>

                          <div className={shared.inline}>
                            <label>
                              開始
                              <input
                                type="month"
                                value={proj.start_date}
                                onChange={(e) =>
                                  updateProjectField(expIndex, clientIndex, projIndex, "start_date", e.target.value)
                                }
                              />
                            </label>
                            <label>
                              参画状況
                              <select
                                value={proj.is_current ? "current" : "ended"}
                                onChange={(e) =>
                                  updateProjectField(expIndex, clientIndex, projIndex, "is_current", e.target.value === "current")
                                }
                              >
                                <option value="ended">終了</option>
                                <option value="current">参画中</option>
                              </select>
                            </label>
                            {!proj.is_current && (
                              <label>
                                終了
                                <input
                                  type="month"
                                  value={proj.end_date}
                                  onChange={(e) =>
                                    updateProjectField(expIndex, clientIndex, projIndex, "end_date", e.target.value)
                                  }
                                />
                              </label>
                            )}
                          </div>

                          <label>
                            役割
                            <input
                              type="text"
                              value={proj.role}
                              onChange={(e) =>
                                updateProjectField(expIndex, clientIndex, projIndex, "role", e.target.value)
                              }
                              placeholder="例: アジャイル開発メンバー"
                            />
                          </label>

                          {/* 体制 */}
                          <div className={styles.stackSection}>
                            <h3>体制</h3>
                            <label>
                              全体人数
                              <div className={styles.inputWithUnit}>
                                <input
                                  type="number"
                                  value={proj.team.total}
                                  onChange={(e) =>
                                    updateTeamTotal(expIndex, clientIndex, projIndex, e.target.value)
                                  }
                                  placeholder="例: 10"
                                />
                                <span className={styles.unit}>名</span>
                              </div>
                            </label>
                            <div className={styles.stackGrid}>
                              {proj.team.members.map((member, memberIndex) => (
                                <div
                                  key={`member-${expIndex}-${clientIndex}-${projIndex}-${memberIndex}`}
                                  className={styles.stackChip}
                                >
                                  <select
                                    className={styles.chipSelect}
                                    value={member.role}
                                    onChange={(e) =>
                                      updateTeamMember(expIndex, clientIndex, projIndex, memberIndex, "role", e.target.value)
                                    }
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
                                      onChange={(e) =>
                                        updateTeamMember(expIndex, clientIndex, projIndex, memberIndex, "count", e.target.value)
                                      }
                                      placeholder="人数"
                                      style={{ width: "5em" }}
                                    />
                                    <span className={styles.unit}>名</span>
                                  </div>
                                  <button
                                    type="button"
                                    className={styles.chipRemove}
                                    onClick={() => removeTeamMember(expIndex, clientIndex, projIndex, memberIndex)}
                                    aria-label="役割を削除"
                                  >
                                    &times;
                                  </button>
                                </div>
                              ))}
                              <button
                                type="button"
                                className={`ghost ${styles.chipAdd}`}
                                onClick={() => addTeamMember(expIndex, clientIndex, projIndex)}
                              >
                                + 役割を追加
                              </button>
                            </div>
                          </div>

                          <label>
                            プロジェクト概要
                            <input
                              type="text"
                              value={proj.description}
                              onChange={(e) =>
                                updateProjectField(expIndex, clientIndex, projIndex, "description", e.target.value)
                              }
                            />
                          </label>

                          <MarkdownTextarea
                            label="課題"
                            value={proj.challenge}
                            onChange={(v) =>
                              updateProjectField(expIndex, clientIndex, projIndex, "challenge", v)
                            }
                            rows={2}
                          />

                          <MarkdownTextarea
                            label="行動"
                            value={proj.action}
                            onChange={(v) =>
                              updateProjectField(expIndex, clientIndex, projIndex, "action", v)
                            }
                            rows={2}
                          />

                          <MarkdownTextarea
                            label="成果"
                            value={proj.result}
                            onChange={(v) =>
                              updateProjectField(expIndex, clientIndex, projIndex, "result", v)
                            }
                            rows={2}
                          />

                          {/* 技術スタック（チップ型） */}
                          <div className={styles.stackSection}>
                            <h3>技術スタック</h3>
                            <div className={styles.stackGrid}>
                              {proj.technology_stacks.map((stack, stackIndex) => (
                                <div
                                  key={`stack-${expIndex}-${clientIndex}-${projIndex}-${stackIndex}`}
                                  className={styles.stackChip}
                                >
                                  <select
                                    className={styles.chipSelect}
                                    value={stack.category}
                                    onChange={(e) =>
                                      updateTechnologyStackField(
                                        expIndex,
                                        clientIndex,
                                        projIndex,
                                        stackIndex,
                                        "category",
                                        e.target.value,
                                      )
                                    }
                                  >
                                    {careerTechnologyStackCategories.map((cat) => (
                                      <option key={cat} value={cat}>
                                        {careerTechnologyStackCategoryLabels[cat]}
                                      </option>
                                    ))}
                                  </select>
                                  <Combobox
                                    value={stack.name}
                                    onChange={(val) =>
                                      updateTechnologyStackField(
                                        expIndex,
                                        clientIndex,
                                        projIndex,
                                        stackIndex,
                                        "name",
                                        val,
                                      )
                                    }
                                    options={techStackNamesByCategory.get(stack.category) ?? []}
                                    placeholder="例: TypeScript"
                                    allowCustom
                                  />
                                  <button
                                    type="button"
                                    className={styles.chipRemove}
                                    onClick={() =>
                                      removeTechnologyStack(expIndex, clientIndex, projIndex, stackIndex)
                                    }
                                    aria-label="技術スタックを削除"
                                  >
                                    &times;
                                  </button>
                                </div>
                              ))}
                              <button
                                type="button"
                                className={`ghost ${styles.chipAdd}`}
                                onClick={() => addTechnologyStack(expIndex, clientIndex, projIndex)}
                              >
                                + 追加
                              </button>
                            </div>
                          </div>

                          {/* 工程 */}
                          <div className={styles.stackSection}>
                            <h3>工程</h3>
                            <div className={styles.stackGrid}>
                              {phaseOptions.map((phase) => (
                                <label
                                  key={`phase-${expIndex}-${clientIndex}-${projIndex}-${phase}`}
                                  className={styles.stackChip}
                                  style={{ cursor: "pointer" }}
                                >
                                  <input
                                    type="checkbox"
                                    checked={proj.phases.includes(phase)}
                                    onChange={() => togglePhase(expIndex, clientIndex, projIndex, phase)}
                                  />
                                  {phase}
                                </label>
                              ))}
                            </div>
                          </div>

                          <button
                            type="button"
                            className="danger"
                            onClick={() => removeProject(expIndex, clientIndex, projIndex)}
                          >
                            プロジェクトを削除
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        className="ghost"
                        onClick={() => addProject(expIndex, clientIndex)}
                      >
                        プロジェクトを追加
                      </button>
                    </div>

                    <button
                      type="button"
                      className="danger"
                      onClick={() => removeClient(expIndex, clientIndex)}
                    >
                      取引先（常駐先）を削除
                    </button>
                  </div>
                ))}
                <button type="button" className="ghost" onClick={() => addClient(expIndex)}>
                  取引先（常駐先）を追加
                </button>
              </div>

              <button type="button" className="danger" onClick={() => removeExperience(expIndex)}>
                職務経歴を削除
              </button>
            </div>
          ))}

          <button type="button" className="ghost" onClick={addExperience}>
            職務経歴を追加
          </button>
        </section>
      </div>
    </div>
  </form>
</>
);
}
