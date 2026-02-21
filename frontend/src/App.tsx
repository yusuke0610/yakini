import { FormEvent, useMemo, useState } from "react";

import { createResume, downloadResumePdf, updateResume } from "./api";
import type { Education, Experience, ResumePayload } from "./types";

const blankExperience: Experience = {
  company: "",
  title: "",
  start_date: "",
  end_date: "",
  description: ""
};

const blankEducation: Education = {
  school: "",
  degree: "",
  start_date: "",
  end_date: ""
};

type ResumeFormState = {
  full_name: string;
  email: string;
  phone: string;
  summary: string;
  experiences: Experience[];
  educations: Education[];
  skillsText: string;
};

type TextFieldKey = "full_name" | "email" | "phone" | "summary" | "skillsText";

function trimExperience(exp: Experience): Experience {
  return {
    company: exp.company.trim(),
    title: exp.title.trim(),
    start_date: exp.start_date.trim(),
    end_date: exp.end_date.trim(),
    description: exp.description.trim()
  };
}

function trimEducation(edu: Education): Education {
  return {
    school: edu.school.trim(),
    degree: edu.degree.trim(),
    start_date: edu.start_date.trim(),
    end_date: edu.end_date.trim()
  };
}

function hasAnyValue(valueMap: Record<string, string>): boolean {
  return Object.values(valueMap).some(Boolean);
}

function hasEmptyValue(valueMap: Record<string, string>): boolean {
  return Object.values(valueMap).some((value) => !value);
}

function buildPayload(state: ResumeFormState): ResumePayload {
  const experiences = state.experiences
    .map(trimExperience)
    .filter((exp) => hasAnyValue(exp));

  const educations = state.educations
    .map(trimEducation)
    .filter((edu) => hasAnyValue(edu));

  const hasIncompleteExperience = experiences.some((exp) => hasEmptyValue(exp));
  if (hasIncompleteExperience) {
    throw new Error("職務経歴は入力する場合、すべての項目を埋めてください。");
  }

  const hasIncompleteEducation = educations.some((edu) => hasEmptyValue(edu));
  if (hasIncompleteEducation) {
    throw new Error("学歴は入力する場合、すべての項目を埋めてください。");
  }

  const skills = state.skillsText
    .split(/[\n,]/)
    .map((skill) => skill.trim())
    .filter(Boolean);

  return {
    full_name: state.full_name.trim(),
    email: state.email.trim(),
    phone: state.phone.trim(),
    summary: state.summary.trim(),
    experiences,
    educations,
    skills
  };
}

export default function App() {
  const [form, setForm] = useState<ResumeFormState>({
    full_name: "",
    email: "",
    phone: "",
    summary: "",
    experiences: [blankExperience],
    educations: [blankEducation],
    skillsText: ""
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

  const onChangeField = (key: TextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const updateExperienceField = (index: number, key: keyof Experience, value: string) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, i) =>
        i === index ? { ...exp, [key]: value } : exp
      )
    }));
  };

  const updateEducationField = (index: number, key: keyof Education, value: string) => {
    setForm((prev) => ({
      ...prev,
      educations: prev.educations.map((edu, i) =>
        i === index ? { ...edu, [key]: value } : edu
      )
    }));
  };

  const addExperience = () => {
    setForm((prev) => ({ ...prev, experiences: [...prev.experiences, { ...blankExperience }] }));
  };

  const removeExperience = (index: number) => {
    setForm((prev) => ({
      ...prev,
      experiences:
        prev.experiences.length === 1
          ? [{ ...blankExperience }]
          : prev.experiences.filter((_, i) => i !== index)
    }));
  };

  const addEducation = () => {
    setForm((prev) => ({ ...prev, educations: [...prev.educations, { ...blankEducation }] }));
  };

  const removeEducation = (index: number) => {
    setForm((prev) => ({
      ...prev,
      educations:
        prev.educations.length === 1
          ? [{ ...blankEducation }]
          : prev.educations.filter((_, i) => i !== index)
    }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = buildPayload(form);
      const saved = resumeId
        ? await updateResume(resumeId, payload)
        : await createResume(payload);

      setResumeId(saved.id);
      setSuccess("職務経歴を保存しました。PDF出力できます。");
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
    if (!resumeId) {
      return;
    }

    setDownloading(true);
    setError(null);
    setSuccess(null);

    try {
      await downloadResumePdf(resumeId);
      setSuccess("PDFをダウンロードしました。");
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

  return (
    <div className="page">
      <main className="container">
        <h1>職務経歴書ビルダー</h1>
        <p className="lead">入力した内容をPostgreSQLに保存し、PDFとして出力できます。</p>

        <form onSubmit={onSubmit} className="form">
          <section className="section">
            <h2>基本情報</h2>
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
              メール
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
            <label>
              概要
              <textarea
                rows={4}
                value={form.summary}
                onChange={(e) => onChangeField("summary", e.target.value)}
                required
              />
            </label>
          </section>

          <section className="section">
            <h2>職務経歴</h2>
            {form.experiences.map((exp, index) => (
              <div key={`exp-${index}`} className="entry">
                <label>
                  会社名
                  <input
                    type="text"
                    value={exp.company}
                    onChange={(e) => updateExperienceField(index, "company", e.target.value)}
                  />
                </label>
                <label>
                  職種
                  <input
                    type="text"
                    value={exp.title}
                    onChange={(e) => updateExperienceField(index, "title", e.target.value)}
                  />
                </label>
                <div className="inline">
                  <label>
                    開始
                    <input
                      type="month"
                      value={exp.start_date}
                      onChange={(e) => updateExperienceField(index, "start_date", e.target.value)}
                    />
                  </label>
                  <label>
                    終了
                    <input
                      type="month"
                      value={exp.end_date}
                      onChange={(e) => updateExperienceField(index, "end_date", e.target.value)}
                    />
                  </label>
                </div>
                <label>
                  業務内容
                  <textarea
                    rows={3}
                    value={exp.description}
                    onChange={(e) =>
                      updateExperienceField(index, "description", e.target.value)
                    }
                  />
                </label>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => removeExperience(index)}
                >
                  この経歴を削除
                </button>
              </div>
            ))}
            <button type="button" className="ghost" onClick={addExperience}>
              経歴を追加
            </button>
          </section>

          <section className="section">
            <h2>学歴</h2>
            {form.educations.map((edu, index) => (
              <div key={`edu-${index}`} className="entry">
                <label>
                  学校名
                  <input
                    type="text"
                    value={edu.school}
                    onChange={(e) => updateEducationField(index, "school", e.target.value)}
                  />
                </label>
                <label>
                  学位/専攻
                  <input
                    type="text"
                    value={edu.degree}
                    onChange={(e) => updateEducationField(index, "degree", e.target.value)}
                  />
                </label>
                <div className="inline">
                  <label>
                    開始
                    <input
                      type="month"
                      value={edu.start_date}
                      onChange={(e) => updateEducationField(index, "start_date", e.target.value)}
                    />
                  </label>
                  <label>
                    終了
                    <input
                      type="month"
                      value={edu.end_date}
                      onChange={(e) => updateEducationField(index, "end_date", e.target.value)}
                    />
                  </label>
                </div>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => removeEducation(index)}
                >
                  この学歴を削除
                </button>
              </div>
            ))}
            <button type="button" className="ghost" onClick={addEducation}>
              学歴を追加
            </button>
          </section>

          <section className="section">
            <h2>スキル</h2>
            <label>
              スキル（改行またはカンマ区切り）
              <textarea
                rows={3}
                value={form.skillsText}
                onChange={(e) => onChangeField("skillsText", e.target.value)}
                placeholder="例: Python, FastAPI, React"
              />
            </label>
          </section>

          <div className="actions">
            <button type="submit" disabled={saving}>
              {saveButtonText}
            </button>
            <button
              type="button"
              onClick={onDownloadPdf}
              disabled={!resumeId || downloading}
            >
              {downloading ? "ダウンロード中..." : "PDF出力"}
            </button>
          </div>

          {resumeId && <p className="hint">保存ID: {resumeId}</p>}
          {error && <p className="error">{error}</p>}
          {success && <p className="success">{success}</p>}
        </form>
      </main>
    </div>
  );
}
