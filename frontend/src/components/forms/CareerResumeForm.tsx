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
import type { CareerFormState } from "../../payloadBuilders";
import type { CareerTechnologyStack, CareerTechnologyStackCategory } from "../../types";
import {
  blankCareerExperience,
  blankCareerProject,
  blankCareerTechnologyStack,
  careerTechnologyStackCategories,
} from "../../constants";
import type {
  CareerTextFieldKey,
  CareerExperienceFieldKey,
  CareerProjectFieldKey,
} from "../../formTypes";
import { usePdfActions } from "../../hooks/usePdfActions";
import { PdfPreviewModal } from "./PdfPreviewModal";

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
              ? latest.experiences.map((exp) => ({
                  ...exp,
                  end_date: exp.end_date ?? "",
                  projects: exp.projects.length > 0 ? exp.projects : [{ ...blankCareerProject }],
                }))
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

  const updateProjectField = (
    expIndex: number,
    projIndex: number,
    key: CareerProjectFieldKey,
    value: string,
  ) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          projects: exp.projects.map((proj, pi) =>
            pi === projIndex ? { ...proj, [key]: value } : proj,
          ),
        };
      }),
    }));
  };

  const updateTechnologyStackField = (
    expIndex: number,
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
          projects: exp.projects.map((proj, pi) => {
            if (pi !== projIndex) return proj;
            return {
              ...proj,
              technology_stacks: proj.technology_stacks.map((stack, si) => {
                if (si !== stackIndex) return stack;
                if (key === "category") {
                  return { ...stack, category: value as CareerTechnologyStackCategory };
                }
                return { ...stack, name: value };
              }),
            };
          }),
        };
      }),
    }));
  };

  const addTechnologyStack = (expIndex: number, projIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          projects: exp.projects.map((proj, pi) =>
            pi === projIndex
              ? {
                  ...proj,
                  technology_stacks: [...proj.technology_stacks, { ...blankCareerTechnologyStack }],
                }
              : proj,
          ),
        };
      }),
    }));
  };

  const removeTechnologyStack = (expIndex: number, projIndex: number, stackIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          projects: exp.projects.map((proj, pi) => {
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
    }));
  };

  const addProject = (expIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) =>
        ei === expIndex
          ? {
              ...exp,
              projects: [
                ...exp.projects,
                { ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] },
              ],
            }
          : exp,
      ),
    }));
  };

  const removeProject = (expIndex: number, projIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          projects:
            exp.projects.length === 1
              ? [{ ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] }]
              : exp.projects.filter((_, pi) => pi !== projIndex),
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
        <div className="pageHeader">
          <h1>職務経歴書</h1>
          <div className="pageHeaderActions">
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

        <div className="pageBody">
          <div className="form">
            {error && <p className="error">{error}</p>}
            {success && <p className="success">{success}</p>}

            <section className="section">
              <label>
                <span className="labelText">職務要約<span className="requiredBadge">必須</span></span>
                <textarea
                  rows={4}
                  value={form.career_summary}
                  onChange={(e) => onChangeField("career_summary", e.target.value)}
                  required
                />
              </label>
              <label>
                <span className="labelText">自己PR<span className="requiredBadge">必須</span></span>
                <textarea
                  rows={4}
                  value={form.self_pr}
                  onChange={(e) => onChangeField("self_pr", e.target.value)}
                  required
                />
              </label>
            </section>

        <section className="section">
          <h2>職務経歴</h2>
          {form.experiences.map((exp, expIndex) => (
            <div key={`exp-${expIndex}`} className="entry">
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

              <div className="inline">
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

              <div className="inline">
                <label>
                  従業員数
                  <div className="inputWithUnit">
                    <input
                      type="number"
                      value={exp.employee_count}
                      onChange={(e) =>
                        updateExperienceField(expIndex, "employee_count", e.target.value)
                      }
                      placeholder="例: 300"
                    />
                    <span className="unit">名</span>
                  </div>
                </label>
                <label>
                  資本金
                  <div className="inputWithUnit">
                    <input
                      type="number"
                      value={exp.capital}
                      onChange={(e) => updateExperienceField(expIndex, "capital", e.target.value)}
                      placeholder="例: 5"
                    />
                    <span className="unit">千万円</span>
                  </div>
                </label>
              </div>

              {/* Projects */}
              <div className="stackSection">
                <h3>プロジェクト</h3>
                {exp.projects.map((proj, projIndex) => (
                  <div key={`proj-${expIndex}-${projIndex}`} className="entry">
                    <label>
                      プロジェクト名
                      <input
                        type="text"
                        value={proj.name}
                        onChange={(e) =>
                          updateProjectField(expIndex, projIndex, "name", e.target.value)
                        }
                        placeholder="例: エネルギー業界 IoT Web API アプリ新規開発"
                      />
                    </label>

                    <div className="inline">
                      <label>
                        役割
                        <input
                          type="text"
                          value={proj.role}
                          onChange={(e) =>
                            updateProjectField(expIndex, projIndex, "role", e.target.value)
                          }
                          placeholder="例: アジャイル開発メンバー"
                        />
                      </label>
                      <label>
                        規模
                        <div className="inputWithUnit">
                          <input
                            type="number"
                            value={proj.scale}
                            onChange={(e) =>
                              updateProjectField(expIndex, projIndex, "scale", e.target.value)
                            }
                            placeholder="例: 10"
                          />
                          <span className="unit">名</span>
                        </div>
                      </label>
                    </div>

                    <label>
                      業務内容
                      <textarea
                        rows={3}
                        value={proj.description}
                        onChange={(e) =>
                          updateProjectField(expIndex, projIndex, "description", e.target.value)
                        }
                      />
                    </label>

                    <label>
                      実績・取り組み
                      <textarea
                        rows={3}
                        value={proj.achievements}
                        onChange={(e) =>
                          updateProjectField(expIndex, projIndex, "achievements", e.target.value)
                        }
                      />
                    </label>

                    <div className="stackSection">
                      <h3>技術スタック</h3>
                      {proj.technology_stacks.map((stack, stackIndex) => (
                        <div
                          key={`stack-${expIndex}-${projIndex}-${stackIndex}`}
                          className="stackEntry"
                        >
                          <div className="inline">
                            <label>
                              区分
                              <select
                                value={stack.category}
                                onChange={(e) =>
                                  updateTechnologyStackField(
                                    expIndex,
                                    projIndex,
                                    stackIndex,
                                    "category",
                                    e.target.value,
                                  )
                                }
                              >
                                {careerTechnologyStackCategories.map((category) => (
                                  <option key={category} value={category}>
                                    {category}
                                  </option>
                                ))}
                              </select>
                            </label>
                            <label>
                              名称
                              <input
                                type="text"
                                value={stack.name}
                                onChange={(e) =>
                                  updateTechnologyStackField(
                                    expIndex,
                                    projIndex,
                                    stackIndex,
                                    "name",
                                    e.target.value,
                                  )
                                }
                                placeholder="例: TypeScript"
                              />
                            </label>
                          </div>
                          <button
                            type="button"
                            className="danger"
                            onClick={() => removeTechnologyStack(expIndex, projIndex, stackIndex)}
                          >
                            技術スタックを削除
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        className="ghost"
                        onClick={() => addTechnologyStack(expIndex, projIndex)}
                      >
                        技術スタックを追加
                      </button>
                    </div>

                    <button
                      type="button"
                      className="danger"
                      onClick={() => removeProject(expIndex, projIndex)}
                    >
                      プロジェクトを削除
                    </button>
                  </div>
                ))}
                <button type="button" className="ghost" onClick={() => addProject(expIndex)}>
                  プロジェクトを追加
                </button>
              </div>

              <button type="button" className="danger" onClick={() => removeExperience(expIndex)}>
                経歴を削除
              </button>
            </div>
          ))}

          <button type="button" className="ghost" onClick={addExperience}>
            経歴を追加
          </button>
        </section>

            {resumeId && <p className="hint">保存ID: {resumeId}</p>}
          </div>
        </div>
      </form>
    </>
  );
}
