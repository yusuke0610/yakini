import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createBasicInfo,
  createCareerResume,
  createResume,
  downloadCareerResumeMarkdown,
  downloadCareerResumePdf,
  downloadResumeMarkdown,
  downloadResumePdf,
  getCareerResumePdfBlobUrl,
  getGitHubOAuthUrl,
  getLatestBasicInfo,
  getResumePdfBlobUrl,
  githubCallback,
  login,
  setAuthToken,
  setOnUnauthorized,
  updateBasicInfo,
  updateCareerResume,
  updateResume
} from "./api";
import {
  buildBasicPayload,
  buildCareerPayload,
  buildResumePayload
} from "./payloadBuilders";
import type {
  BasicFormState,
  CareerExperienceForm,
  CareerFormState,
  CareerProjectForm,
  ResumeFormState
} from "./payloadBuilders";
import type {
  BasicQualification,
  CareerTechnologyStack,
  CareerTechnologyStackCategory,
  ResumeHistory
} from "./types";

type PageKey = "basic" | "career" | "Resume";

type BasicTextFieldKey = "full_name" | "record_date";

type CareerTextFieldKey = "career_summary" | "self_pr";
type CareerExperienceFieldKey = "company" | "business_description" | "start_date" | "end_date" | "is_current" | "employee_count" | "capital";
type CareerProjectFieldKey = "name" | "role" | "description" | "achievements" | "scale";

type ResumeTextFieldKey =
  | "postal_code"
  | "prefecture"
  | "address"
  | "email"
  | "phone"
  | "motivation";

const blankBasicQualification: BasicQualification = {
  acquired_date: "",
  name: ""
};

const careerTechnologyStackCategories: CareerTechnologyStackCategory[] = [
  "言語",
  "フレームワーク",
  "OS",
  "DB",
  "クラウドリソース",
  "開発支援ツール"
];

const blankCareerTechnologyStack: CareerTechnologyStack = {
  category: "言語",
  name: ""
};

const blankCareerProject: CareerProjectForm = {
  name: "",
  role: "",
  description: "",
  achievements: "",
  scale: "",
  technology_stacks: [{ ...blankCareerTechnologyStack }]
};

const blankCareerExperience: CareerExperienceForm = {
  company: "",
  business_description: "",
  start_date: "",
  end_date: "",
  is_current: false,
  employee_count: "",
  capital: "",
  projects: [{ ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] }]
};

const blankHistory: ResumeHistory = {
  date: "",
  name: ""
};

function BasicInfoForm() {
  const [form, setForm] = useState<BasicFormState>({
    full_name: "",
    record_date: "",
    qualifications: [{ ...blankBasicQualification }]
  });
  const [basicInfoId, setBasicInfoId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const latest = await getLatestBasicInfo();
        if (!active) {
          return;
        }
        setBasicInfoId(latest.id);
        setForm({
          full_name: latest.full_name,
          record_date: latest.record_date,
          qualifications:
            latest.qualifications.length > 0
              ? latest.qualifications
              : [{ ...blankBasicQualification }]
        });
      } catch {
        if (!active) {
          return;
        }
      } finally {
        if (active) {
          setLoading(false);
        }
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
    return basicInfoId ? "更新する" : "保存する";
  }, [basicInfoId, saving]);

  const onChangeField = (key: BasicTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const updateQualificationField = (
    index: number,
    key: keyof BasicQualification,
    value: string
  ) => {
    setForm((prev) => ({
      ...prev,
      qualifications: prev.qualifications.map((qualification, i) =>
        i === index ? { ...qualification, [key]: value } : qualification
      )
    }));
  };

  const addQualification = () => {
    setForm((prev) => ({
      ...prev,
      qualifications: [...prev.qualifications, { ...blankBasicQualification }]
    }));
  };

  const removeQualification = (index: number) => {
    setForm((prev) => ({
      ...prev,
      qualifications:
        prev.qualifications.length === 1
          ? [{ ...blankBasicQualification }]
          : prev.qualifications.filter((_, i) => i !== index)
    }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = buildBasicPayload(form);
      const saved = basicInfoId
        ? await updateBasicInfo(basicInfoId, payload)
        : await createBasicInfo(payload);
      setBasicInfoId(saved.id);
      setSuccess("基本情報を保存しました。");
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "保存中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="hint">基本情報を読み込み中です...</p>;
  }

  return (
    <form onSubmit={onSubmit} className="form">
      <section className="section">
        <label>
          氏名
          <input
            type="text"
            value={form.full_name}
            onChange={(e) => onChangeField("full_name", e.target.value)}
            required
          />
        </label>
        <label>
          記載日
          <input
            type="date"
            value={form.record_date}
            onChange={(e) => onChangeField("record_date", e.target.value)}
            required
          />
        </label>
      </section>

      <section className="section">
        <h2>資格</h2>
        {form.qualifications.map((qualification, index) => (
          <div key={`basic-qualification-${index}`} className="entry">
            <div className="inline">
              <label>
                資格名
                <input
                  type="text"
                  value={qualification.name}
                  onChange={(e) => updateQualificationField(index, "name", e.target.value)}
                />
              </label>
              <label>
                取得日
                <input
                  type="date"
                  value={qualification.acquired_date}
                  onChange={(e) =>
                    updateQualificationField(index, "acquired_date", e.target.value)
                  }
                />
              </label>
            </div>
            <button type="button" className="danger" onClick={() => removeQualification(index)}>
              資格を削除
            </button>
          </div>
        ))}

        <button type="button" className="ghost" onClick={addQualification}>
          資格を追加
        </button>
      </section>

      <div className="actions">
        <button type="submit" disabled={saving}>
          {saveButtonText}
        </button>
      </div>

      {basicInfoId && <p className="hint">保存ID: {basicInfoId}</p>}
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </form>
  );
}

function CareerResumeForm() {
  const [form, setForm] = useState<CareerFormState>({
    career_summary: "",
    self_pr: "",
    experiences: [{ ...blankCareerExperience }]
  });
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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
    value: string | boolean
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
      })
    }));
  };

  const updateProjectField = (
    expIndex: number,
    projIndex: number,
    key: CareerProjectFieldKey,
    value: string
  ) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) => {
        if (ei !== expIndex) return exp;
        return {
          ...exp,
          projects: exp.projects.map((proj, pi) =>
            pi === projIndex ? { ...proj, [key]: value } : proj
          )
        };
      })
    }));
  };

  const updateTechnologyStackField = (
    expIndex: number,
    projIndex: number,
    stackIndex: number,
    key: keyof CareerTechnologyStack,
    value: string
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
              })
            };
          })
        };
      })
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
              ? { ...proj, technology_stacks: [...proj.technology_stacks, { ...blankCareerTechnologyStack }] }
              : proj
          )
        };
      })
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
                  : proj.technology_stacks.filter((_, si) => si !== stackIndex)
            };
          })
        };
      })
    }));
  };

  const addProject = (expIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, ei) =>
        ei === expIndex
          ? { ...exp, projects: [...exp.projects, { ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] }] }
          : exp
      )
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
              : exp.projects.filter((_, pi) => pi !== projIndex)
        };
      })
    }));
  };

  const addExperience = () => {
    setForm((prev) => ({ ...prev, experiences: [...prev.experiences, { ...blankCareerExperience }] }));
  };

  const removeExperience = (index: number) => {
    setForm((prev) => ({
      ...prev,
      experiences:
        prev.experiences.length === 1
          ? [{ ...blankCareerExperience }]
          : prev.experiences.filter((_, i) => i !== index)
    }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = buildCareerPayload(form);
      const saved = resumeId
        ? await updateCareerResume(resumeId, payload)
        : await createCareerResume(payload);

      setResumeId(saved.id);
      setSuccess("職務経歴書を保存しました。PDF出力できます。");
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "保存中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const onDownloadPdf = async () => {
    if (!resumeId) return;
    setDownloading(true);
    setError(null);
    setSuccess(null);

    try {
      await downloadCareerResumePdf(resumeId);
      setSuccess("職務経歴書PDFをダウンロードしました。");
    } catch (downloadError) {
      const message =
        downloadError instanceof Error
          ? downloadError.message
          : "PDFダウンロード中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setDownloading(false);
    }
  };

  const onDownloadMarkdown = async () => {
    if (!resumeId) return;
    setError(null);
    try {
      await downloadCareerResumeMarkdown(resumeId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Markdownダウンロードに失敗しました。");
    }
  };

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onPreviewPdf = async () => {
    if (!resumeId) return;
    setError(null);
    try {
      const url = await getCareerResumePdfBlobUrl(resumeId);
      setPreviewUrl(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "プレビューに失敗しました。");
    }
  };

  return (
    <>
    {previewUrl && (
      <div className="previewOverlay" onClick={() => { URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }}>
        <div className="previewModal" onClick={(e) => e.stopPropagation()}>
          <div className="previewHeader">
            <span>PDFプレビュー</span>
            <button type="button" onClick={() => { URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }}>閉じる</button>
          </div>
          <iframe src={previewUrl} className="previewFrame" title="PDF Preview" />
        </div>
      </div>
    )}
    <form onSubmit={onSubmit} className="form">
      <section className="section">
        <label>
          職務要約
          <textarea
            rows={4}
            value={form.career_summary}
            onChange={(e) => onChangeField("career_summary", e.target.value)}
            required
          />
        </label>
        <label>
          自己PR
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
                onChange={(e) => updateExperienceField(expIndex, "business_description", e.target.value)}
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
                    onChange={(e) => updateExperienceField(expIndex, "employee_count", e.target.value)}
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
                      onChange={(e) => updateProjectField(expIndex, projIndex, "name", e.target.value)}
                      placeholder="例: エネルギー業界 IoT Web API アプリ新規開発"
                    />
                  </label>

                  <div className="inline">
                    <label>
                      役割
                      <input
                        type="text"
                        value={proj.role}
                        onChange={(e) => updateProjectField(expIndex, projIndex, "role", e.target.value)}
                        placeholder="例: アジャイル開発メンバー"
                      />
                    </label>
                    <label>
                      規模
                      <div className="inputWithUnit">
                        <input
                          type="number"
                          value={proj.scale}
                          onChange={(e) => updateProjectField(expIndex, projIndex, "scale", e.target.value)}
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
                      onChange={(e) => updateProjectField(expIndex, projIndex, "description", e.target.value)}
                    />
                  </label>

                  <label>
                    実績・取り組み
                    <textarea
                      rows={3}
                      value={proj.achievements}
                      onChange={(e) => updateProjectField(expIndex, projIndex, "achievements", e.target.value)}
                    />
                  </label>

                  <div className="stackSection">
                    <h3>技術スタック</h3>
                    {proj.technology_stacks.map((stack, stackIndex) => (
                      <div key={`stack-${expIndex}-${projIndex}-${stackIndex}`} className="stackEntry">
                        <div className="inline">
                          <label>
                            区分
                            <select
                              value={stack.category}
                              onChange={(e) =>
                                updateTechnologyStackField(expIndex, projIndex, stackIndex, "category", e.target.value)
                              }
                            >
                              {careerTechnologyStackCategories.map((category) => (
                                <option key={category} value={category}>{category}</option>
                              ))}
                            </select>
                          </label>
                          <label>
                            名称
                            <input
                              type="text"
                              value={stack.name}
                              onChange={(e) =>
                                updateTechnologyStackField(expIndex, projIndex, stackIndex, "name", e.target.value)
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
                    <button type="button" className="ghost" onClick={() => addTechnologyStack(expIndex, projIndex)}>
                      技術スタックを追加
                    </button>
                  </div>

                  <button type="button" className="danger" onClick={() => removeProject(expIndex, projIndex)}>
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

      <div className="actions">
        <button type="submit" disabled={saving}>
          {saveButtonText}
        </button>
        <button type="button" onClick={onPreviewPdf} disabled={!resumeId}>
          プレビュー
        </button>
        <button type="button" onClick={onDownloadPdf} disabled={!resumeId || downloading}>
          {downloading ? "ダウンロード中..." : "PDF出力"}
        </button>
        <button type="button" onClick={onDownloadMarkdown} disabled={!resumeId}>
          Markdown出力
        </button>
      </div>

      {resumeId && <p className="hint">保存ID: {resumeId}</p>}
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </form>
    </>
  );
}

function ResumeForm() {
  const [form, setForm] = useState<ResumeFormState>({
    postal_code: "",
    prefecture: "",
    address: "",
    email: "",
    phone: "",
    motivation: "",
    educations: [{ ...blankHistory }],
    work_histories: [{ ...blankHistory }],
    photo: null
  });
  const [ResumeId, setResumeId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const saveButtonText = useMemo(() => {
    if (saving) {
      return "保存中...";
    }
    return ResumeId ? "更新する" : "保存する";
  }, [ResumeId, saving]);

  const onChangeField = (key: ResumeTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const onPhotoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setForm((prev) => ({ ...prev, photo: reader.result as string }));
    };
    reader.readAsDataURL(file);
  };

  const removePhoto = () => {
    setForm((prev) => ({ ...prev, photo: null }));
  };

  const updateEducationField = (index: number, key: keyof ResumeHistory, value: string) => {
    setForm((prev) => ({
      ...prev,
      educations: prev.educations.map((education, i) =>
        i === index ? { ...education, [key]: value } : education
      )
    }));
  };

  const updateWorkHistoryField = (
    index: number,
    key: keyof ResumeHistory,
    value: string
  ) => {
    setForm((prev) => ({
      ...prev,
      work_histories: prev.work_histories.map((workHistory, i) =>
        i === index ? { ...workHistory, [key]: value } : workHistory
      )
    }));
  };

  const addEducation = () => {
    setForm((prev) => ({ ...prev, educations: [...prev.educations, { ...blankHistory }] }));
  };

  const removeEducation = (index: number) => {
    setForm((prev) => ({
      ...prev,
      educations:
        prev.educations.length === 1
          ? [{ ...blankHistory }]
          : prev.educations.filter((_, i) => i !== index)
    }));
  };

  const addWorkHistory = () => {
    setForm((prev) => ({
      ...prev,
      work_histories: [...prev.work_histories, { ...blankHistory }]
    }));
  };

  const removeWorkHistory = (index: number) => {
    setForm((prev) => ({
      ...prev,
      work_histories:
        prev.work_histories.length === 1
          ? [{ ...blankHistory }]
          : prev.work_histories.filter((_, i) => i !== index)
    }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = buildResumePayload(form);
      const saved = ResumeId
        ? await updateResume(ResumeId, payload)
        : await createResume(payload);

      setResumeId(saved.id);
      setSuccess("履歴書を保存しました。PDF出力できます。");
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "保存中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const onDownloadPdf = async () => {
    if (!ResumeId) {
      return;
    }

    setDownloading(true);
    setError(null);
    setSuccess(null);

    try {
      await downloadResumePdf(ResumeId);
      setSuccess("履歴書PDFをダウンロードしました。");
    } catch (downloadError) {
      const message =
        downloadError instanceof Error
          ? downloadError.message
          : "PDFダウンロード中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setDownloading(false);
    }
  };

  const onDownloadMarkdown = async () => {
    if (!ResumeId) return;
    setError(null);
    try {
      await downloadResumeMarkdown(ResumeId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Markdownダウンロードに失敗しました。");
    }
  };

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onPreviewPdf = async () => {
    if (!ResumeId) return;
    setError(null);
    try {
      const url = await getResumePdfBlobUrl(ResumeId);
      setPreviewUrl(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "プレビューに失敗しました。");
    }
  };

  return (
    <>
    {previewUrl && (
      <div className="previewOverlay" onClick={() => { URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }}>
        <div className="previewModal" onClick={(e) => e.stopPropagation()}>
          <div className="previewHeader">
            <span>PDFプレビュー</span>
            <button type="button" onClick={() => { URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }}>閉じる</button>
          </div>
          <iframe src={previewUrl} className="previewFrame" title="PDF Preview" />
        </div>
      </div>
    )}
    <form onSubmit={onSubmit} className="form">
      <section className="section">
        <h2>証明写真</h2>
        <div className="photoUpload">
          {form.photo ? (
            <img src={form.photo} alt="証明写真" className="photoPreview" />
          ) : (
            <div className="photoPlaceholder">未選択</div>
          )}
          <div>
            <input type="file" accept="image/*" onChange={onPhotoChange} />
            {form.photo && (
              <button type="button" className="danger" onClick={removePhoto} style={{ marginTop: "0.5rem" }}>
                写真を削除
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="inline">
          <label>
            郵便番号
            <input
              type="text"
              value={form.postal_code}
              onChange={(e) => onChangeField("postal_code", e.target.value)}
              placeholder="例: 150-0001"
              required
            />
          </label>
          <label>
            都道府県
            <input
              type="text"
              value={form.prefecture}
              onChange={(e) => onChangeField("prefecture", e.target.value)}
              placeholder="例: 東京都"
              required
            />
          </label>
        </div>
        <label>
          住所
          <input
            type="text"
            value={form.address}
            onChange={(e) => onChangeField("address", e.target.value)}
            required
          />
        </label>
        <div className="inline">
          <label>
            メールアドレス
            <input
              type="email"
              value={form.email}
              onChange={(e) => onChangeField("email", e.target.value)}
              required
            />
          </label>
          <label>
            電話番号
            <input
              type="text"
              value={form.phone}
              onChange={(e) => onChangeField("phone", e.target.value)}
              required
            />
          </label>
        </div>
        <label>
          志望動機
          <textarea
            rows={4}
            value={form.motivation}
            onChange={(e) => onChangeField("motivation", e.target.value)}
            required
          />
        </label>
      </section>

      <section className="section">
        <h2>学歴</h2>
        {form.educations.map((education, index) => (
          <div key={`education-${index}`} className="entry">
            <div className="inline">
              <label>
                日付
                <input
                  type="month"
                  value={education.date}
                  onChange={(e) => updateEducationField(index, "date", e.target.value)}
                />
              </label>
              <label>
                名称
                <input
                  type="text"
                  value={education.name}
                  onChange={(e) => updateEducationField(index, "name", e.target.value)}
                />
              </label>
            </div>
            <button type="button" className="danger" onClick={() => removeEducation(index)}>
            学歴を削除
            </button>
          </div>
        ))}
        <button type="button" className="ghost" onClick={addEducation}>
          学歴を追加
        </button>
      </section>

      <section className="section">
        <h2>職歴</h2>
        {form.work_histories.map((workHistory, index) => (
          <div key={`work-${index}`} className="entry">
            <div className="inline">
              <label>
                日付
                <input
                  type="month"
                  value={workHistory.date}
                  onChange={(e) => updateWorkHistoryField(index, "date", e.target.value)}
                />
              </label>
              <label>
                名称
                <input
                  type="text"
                  value={workHistory.name}
                  onChange={(e) => updateWorkHistoryField(index, "name", e.target.value)}
                />
              </label>
            </div>
            <button type="button" className="danger" onClick={() => removeWorkHistory(index)}>
              職歴を削除
            </button>
          </div>
        ))}
        <button type="button" className="ghost" onClick={addWorkHistory}>
          職歴を追加
        </button>
      </section>

      <div className="actions">
        <button type="submit" disabled={saving}>
          {saveButtonText}
        </button>
        <button type="button" onClick={onPreviewPdf} disabled={!ResumeId}>
          プレビュー
        </button>
        <button type="button" onClick={onDownloadPdf} disabled={!ResumeId || downloading}>
          {downloading ? "ダウンロード中..." : "PDF出力"}
        </button>
        <button type="button" onClick={onDownloadMarkdown} disabled={!ResumeId}>
          Markdown出力
        </button>
      </div>

      {ResumeId && <p className="hint">保存ID: {ResumeId}</p>}
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </form>
    </>
  );
}

function LoginForm({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await login(username, password);
      onLogin(result.access_token);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "ログインに失敗しました。";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <main className="container">
        <header className="topHeader">
          <h1>ログイン</h1>
        </header>
        <form onSubmit={onSubmit} className="form">
          <section className="section">
            <label>
              ユーザー名
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </label>
            <label>
              パスワード
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </label>
          </section>
          <div className="actions">
            <button type="submit" disabled={loading}>
              {loading ? "ログイン中..." : "ログイン"}
            </button>
          </div>
          <div className="actions" style={{ marginTop: "1rem" }}>
            <button type="button" className="githubLogin" onClick={() => { window.location.href = getGitHubOAuthUrl(); }}>
              Login with GitHub
            </button>
          </div>
          {error && <p className="error">{error}</p>}
        </form>
      </main>
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("auth_token")
  );
  const [page, setPage] = useState<PageKey>("basic");

  useEffect(() => {
    const saved = localStorage.getItem("auth_token");
    if (saved) {
      setAuthToken(saved);
    }
    setOnUnauthorized(() => {
      localStorage.removeItem("auth_token");
      setAuthToken(null);
      setToken(null);
    });

    // Handle GitHub OAuth callback
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (code && !saved) {
      window.history.replaceState({}, "", window.location.pathname);
      githubCallback(code).then((result) => {
        handleLogin(result.access_token);
      }).catch(() => {
        // GitHub OAuth failed, user can retry
      });
    }
  }, []);

  const handleLogin = (newToken: string) => {
    localStorage.setItem("auth_token", newToken);
    setAuthToken(newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    setAuthToken(null);
    setToken(null);
  };

  if (!token) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <div className="page">
      <main className="container">
        <header className="topHeader">
          <h1>
            {page === "basic"
              ? "基本情報"
              : page === "career"
                ? "職務経歴書"
                : "履歴書"}
          </h1>
          <div className="tabRow">
            <button
              type="button"
              className={`tabButton ${page === "basic" ? "active" : ""}`}
              onClick={() => setPage("basic")}
            >
              基本情報
            </button>
            <button
              type="button"
              className={`tabButton ${page === "career" ? "active" : ""}`}
              onClick={() => setPage("career")}
            >
              職務経歴書
            </button>
            <button
              type="button"
              className={`tabButton ${page === "Resume" ? "active" : ""}`}
              onClick={() => setPage("Resume")}
            >
              履歴書
            </button>
            <button
              type="button"
              className="tabButton"
              onClick={handleLogout}
            >
              ログアウト
            </button>
          </div>
        </header>

        <section hidden={page !== "basic"} className="pagePanel" aria-hidden={page !== "basic"}>
          <BasicInfoForm />
        </section>
        <section hidden={page !== "career"} className="pagePanel" aria-hidden={page !== "career"}>
          <CareerResumeForm />
        </section>
        <section
          hidden={page !== "Resume"}
          className="pagePanel"
          aria-hidden={page !== "Resume"}
        >
          <ResumeForm />
        </section>
      </main>
    </div>
  );
}
