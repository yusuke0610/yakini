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
import {
  blankCareerClient,
  blankCareerExperience,
  blankCareerProject,
  blankCareerTechnologyStack,
} from "../../constants";
import type {
  CareerTextFieldKey,
  CareerExperienceFieldKey,
  CareerClientFieldKey,
} from "../../formTypes";
import { useTechnologyStacks } from "../../hooks/useMasterData";
import { usePdfActions } from "../../hooks/usePdfActions";
import shared from "../../styles/shared.module.css";
import { MarkdownTextarea } from "./MarkdownTextarea";
import { PdfPreviewModal } from "./PdfPreviewModal";
import { ProjectModal } from "./ProjectModal";
import styles from "./CareerResumeForm.module.css";

/** プロジェクトモーダルの対象を表す型 */
type ProjectModalTarget = {
  expIndex: number;
  clientIndex: number;
  /** nullの場合は新規追加 */
  projIndex: number | null;
};

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
  const [modalTarget, setModalTarget] = useState<ProjectModalTarget | null>(null);

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
                        has_client: (c as Record<string, unknown>).has_client !== false,
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
                              /* members.count を文字列に変換（APIは数値で返す） */
                              const team = patched.team as Record<string, unknown>;
                              if (Array.isArray(team.members)) {
                                team.members = (team.members as Record<string, unknown>[]).map(
                                  (m) => ({ ...m, count: String(m.count ?? "") }),
                                );
                              }
                              team.total = String(team.total ?? "");
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

  /** モーダルからプロジェクトを保存するコールバック */
  const handleProjectSave = (project: CareerProjectForm) => {
    if (!modalTarget) return;
    const { expIndex, clientIndex, projIndex } = modalTarget;
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
    setModalTarget(null);
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

  /** モーダルに渡すプロジェクトデータを取得する */
  const modalProject = modalTarget
    ? modalTarget.projIndex !== null
      ? form.experiences[modalTarget.expIndex]?.clients[modalTarget.clientIndex]?.projects[
      modalTarget.projIndex
      ] ?? null
      : null
    : null;

  /** プロジェクトのサマリーテキストを生成する */
  const projectSummary = (proj: CareerProjectForm) => {
    const period = [proj.start_date, proj.is_current ? "現在" : proj.end_date]
      .filter(Boolean)
      .join(" 〜 ");
    return period || "";
  };

  return (
    <>
      {previewUrl && <PdfPreviewModal previewUrl={previewUrl} onClose={closePreview} />}
      {modalTarget && (
        <ProjectModal
          project={modalProject}
          onSave={handleProjectSave}
          onClose={() => setModalTarget(null)}
          techStackNamesByCategory={techStackNamesByCategory}
        />
      )}
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

                  {/* 取引先 */}
                  <div className={styles.stackSection}>
                    <h3>取引先</h3>
                    {exp.clients.map((client, clientIndex) => (
                      <div key={`client-${expIndex}-${clientIndex}`} className={shared.entry}>
                        <div className={styles.clientHeader}>
                          {client.has_client && (
                            <label className={styles.clientNameLabel}>
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
                          )}
                          <label className={styles.clientCheckbox}>
                            <input
                              type="checkbox"
                              checked={!client.has_client}
                              onChange={(e) =>
                                updateClientHasClient(expIndex, clientIndex, !e.target.checked)
                              }
                            />
                            取引先なし
                          </label>
                        </div>
                        {/* プロジェクト一覧（サマリー表示） */}
                        <div className={styles.stackSection}>
                          <h3>プロジェクト</h3>
                          {client.projects.map((proj, projIndex) => (
                            <div
                              key={`proj-${expIndex}-${clientIndex}-${projIndex}`}
                              className={styles.projectSummaryRow}
                            >
                              <span className={styles.projectName}>
                                {proj.name || "(未入力)"}
                              </span>
                              <span className={styles.projectPeriod}>
                                {projectSummary(proj)}
                              </span>
                              <div className={styles.projectActions}>
                                <button
                                  type="button"
                                  onClick={() =>
                                    setModalTarget({ expIndex, clientIndex, projIndex })
                                  }
                                >
                                  編集
                                </button>
                                <button
                                  type="button"
                                  className="danger"
                                  onClick={() => removeProject(expIndex, clientIndex, projIndex)}
                                >
                                  削除
                                </button>
                              </div>
                            </div>
                          ))}
                          <button
                            type="button"
                            className="ghost"
                            onClick={() =>
                              setModalTarget({ expIndex, clientIndex, projIndex: null })
                            }
                          >
                            プロジェクトを追加
                          </button>
                        </div>

                        <button
                          type="button"
                          className="danger"
                          onClick={() => removeClient(expIndex, clientIndex)}
                        >
                          取引先を削除
                        </button>
                      </div>
                    ))}
                    <button type="button" className="ghost" onClick={() => addClient(expIndex)}>
                      取引先を追加
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
