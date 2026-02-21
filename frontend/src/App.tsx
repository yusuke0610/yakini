import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createBasicInfo,
  createCareerResume,
  createRirekisho,
  downloadCareerResumePdf,
  downloadRirekishoPdf,
  getLatestBasicInfo,
  updateBasicInfo,
  updateCareerResume,
  updateRirekisho
} from "./api";
import type {
  BasicInfoPayload,
  BasicQualification,
  CareerExperience,
  CareerTechnologyStack,
  CareerTechnologyStackCategory,
  CareerResumePayload,
  RirekishoHistory,
  RirekishoPayload
} from "./types";

type PageKey = "basic" | "career" | "rirekisho";

type BasicFormState = {
  full_name: string;
  record_date: string;
  qualifications: BasicQualification[];
};

type BasicTextFieldKey = "full_name" | "record_date";

type CareerExperienceForm = {
  company: string;
  title: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  description: string;
  achievements: string;
  employee_count: string;
  capital: string;
  technology_stacks: CareerTechnologyStack[];
};

type CareerFormState = {
  career_summary: string;
  self_pr: string;
  experiences: CareerExperienceForm[];
};

type CareerTextFieldKey = "career_summary" | "self_pr";
type CareerExperienceFieldKey = Exclude<keyof CareerExperienceForm, "technology_stacks">;

type RirekishoFormState = {
  postal_code: string;
  prefecture: string;
  address: string;
  email: string;
  phone: string;
  motivation: string;
  educations: RirekishoHistory[];
  work_histories: RirekishoHistory[];
};

type RirekishoTextFieldKey =
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

const blankCareerExperience: CareerExperienceForm = {
  company: "",
  title: "",
  start_date: "",
  end_date: "",
  is_current: false,
  description: "",
  achievements: "",
  employee_count: "",
  capital: "",
  technology_stacks: [{ ...blankCareerTechnologyStack }]
};

const blankHistory: RirekishoHistory = {
  date: "",
  name: ""
};

function hasAnyText(values: Array<string | null | undefined>): boolean {
  return values.some((value) => Boolean(value?.trim()));
}

function buildBasicPayload(state: BasicFormState): BasicInfoPayload {
  const payload: BasicInfoPayload = {
    full_name: state.full_name.trim(),
    record_date: state.record_date.trim(),
    qualifications: state.qualifications
      .map((qualification) => ({
        acquired_date: qualification.acquired_date.trim(),
        name: qualification.name.trim()
      }))
      .filter((qualification) => hasAnyText([qualification.acquired_date, qualification.name]))
  };

  if (!payload.full_name || !payload.record_date) {
    throw new Error("氏名と記載日は必須です。");
  }

  for (const qualification of payload.qualifications) {
    if (!qualification.acquired_date || !qualification.name) {
      throw new Error("資格は取得日と名称を両方入力してください。");
    }
  }

  return payload;
}

function buildCareerPayload(state: CareerFormState): CareerResumePayload {
  const career_summary = state.career_summary.trim();
  if (!career_summary) {
    throw new Error("職務要約を入力してください。");
  }

  const self_pr = state.self_pr.trim();
  if (!self_pr) {
    throw new Error("自己PRを入力してください。");
  }

  const experiences: CareerExperience[] = state.experiences
    .map((exp) => ({
      company: exp.company.trim(),
      title: exp.title.trim(),
      start_date: exp.start_date.trim(),
      end_date: exp.is_current ? null : exp.end_date.trim(),
      is_current: exp.is_current,
      description: exp.description.trim(),
      achievements: exp.achievements.trim(),
      employee_count: exp.employee_count.trim(),
      capital: exp.capital.trim(),
      technology_stacks: exp.technology_stacks
        .map((stack) => ({
          category: stack.category,
          name: stack.name.trim()
        }))
        .filter((stack) => Boolean(stack.name))
    }))
    .filter((exp) =>
      hasAnyText([
        exp.company,
        exp.title,
        exp.start_date,
        exp.end_date ?? "",
        exp.description,
        exp.achievements,
        exp.employee_count,
        exp.capital,
        ...exp.technology_stacks.map((stack) => stack.name)
      ])
    );

  for (const exp of experiences) {
    if (
      !exp.company ||
      !exp.title ||
      !exp.start_date ||
      !exp.description ||
      !exp.achievements ||
      !exp.employee_count ||
      !exp.capital
    ) {
      throw new Error("職務経歴は入力する場合、必須項目をすべて埋めてください。");
    }
    if (!exp.is_current && !exp.end_date) {
      throw new Error("職務経歴の離職年月を入力するか、在職を選択してください。");
    }
  }

  return {
    career_summary,
    self_pr,
    experiences
  };
}

function buildRirekishoPayload(state: RirekishoFormState): RirekishoPayload {
  const payload: RirekishoPayload = {
    postal_code: state.postal_code.trim(),
    prefecture: state.prefecture.trim(),
    address: state.address.trim(),
    email: state.email.trim(),
    phone: state.phone.trim(),
    motivation: state.motivation.trim(),
    educations: state.educations
      .map((education) => ({
        date: education.date.trim(),
        name: education.name.trim()
      }))
      .filter((education) => hasAnyText([education.date, education.name])),
    work_histories: state.work_histories
      .map((workHistory) => ({
        date: workHistory.date.trim(),
        name: workHistory.name.trim()
      }))
      .filter((workHistory) => hasAnyText([workHistory.date, workHistory.name]))
  };

  if (
    !payload.postal_code ||
    !payload.prefecture ||
    !payload.address ||
    !payload.email ||
    !payload.phone ||
    !payload.motivation
  ) {
    throw new Error("郵便番号、都道府県、住所、メールアドレス、電話番号、志望動機は必須です。");
  }

  for (const education of payload.educations) {
    if (!education.date || !education.name) {
      throw new Error("学歴は日付と名称を両方入力してください。");
    }
  }

  for (const workHistory of payload.work_histories) {
    if (!workHistory.date || !workHistory.name) {
      throw new Error("職歴は日付と名称を両方入力してください。");
    }
  }

  return payload;
}

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
                取得日
                <input
                  type="date"
                  value={qualification.acquired_date}
                  onChange={(e) =>
                    updateQualificationField(index, "acquired_date", e.target.value)
                  }
                />
              </label>
              <label>
                名称
                <input
                  type="text"
                  value={qualification.name}
                  onChange={(e) => updateQualificationField(index, "name", e.target.value)}
                />
              </label>
            </div>
            <button type="button" className="ghost" onClick={() => removeQualification(index)}>
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
        if (i !== index) {
          return exp;
        }
        if (key === "is_current") {
          const isCurrent = Boolean(value);
          return {
            ...exp,
            is_current: isCurrent,
            end_date: isCurrent ? "" : exp.end_date
          };
        }
        return { ...exp, [key]: value };
      })
    }));
  };

  const updateTechnologyStackField = (
    experienceIndex: number,
    stackIndex: number,
    key: keyof CareerTechnologyStack,
    value: string
  ) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, index) => {
        if (index !== experienceIndex) {
          return exp;
        }

        return {
          ...exp,
          technology_stacks: exp.technology_stacks.map((stack, i) => {
            if (i !== stackIndex) {
              return stack;
            }
            if (key === "category") {
              return {
                ...stack,
                category: value as CareerTechnologyStackCategory
              };
            }
            return {
              ...stack,
              name: value
            };
          })
        };
      })
    }));
  };

  const addTechnologyStack = (experienceIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, index) =>
        index === experienceIndex
          ? {
              ...exp,
              technology_stacks: [...exp.technology_stacks, { ...blankCareerTechnologyStack }]
            }
          : exp
      )
    }));
  };

  const removeTechnologyStack = (experienceIndex: number, stackIndex: number) => {
    setForm((prev) => ({
      ...prev,
      experiences: prev.experiences.map((exp, index) => {
        if (index !== experienceIndex) {
          return exp;
        }

        return {
          ...exp,
          technology_stacks:
            exp.technology_stacks.length === 1
              ? [{ ...blankCareerTechnologyStack }]
              : exp.technology_stacks.filter((_, i) => i !== stackIndex)
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
    if (!resumeId) {
      return;
    }

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

  return (
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
                在職の有無
                <select
                  value={exp.is_current ? "current" : "ended"}
                  onChange={(e) =>
                    updateExperienceField(index, "is_current", e.target.value === "current")
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
                    onChange={(e) => updateExperienceField(index, "end_date", e.target.value)}
                  />
                </label>
              )}
            </div>

            <div className="inline">
              <label>
                従業員数
                <input
                  type="text"
                  value={exp.employee_count}
                  onChange={(e) => updateExperienceField(index, "employee_count", e.target.value)}
                  placeholder="例: 300名"
                />
              </label>
              <label>
                資本金
                <input
                  type="text"
                  value={exp.capital}
                  onChange={(e) => updateExperienceField(index, "capital", e.target.value)}
                  placeholder="例: 1億円"
                />
              </label>
            </div>

            <label>
              実績
              <textarea
                rows={3}
                value={exp.achievements}
                onChange={(e) => updateExperienceField(index, "achievements", e.target.value)}
              />
            </label>

            <label>
              業務内容
              <textarea
                rows={3}
                value={exp.description}
                onChange={(e) => updateExperienceField(index, "description", e.target.value)}
              />
            </label>

            <div className="stackSection">
              <h3>技術スタック</h3>
              {exp.technology_stacks.map((stack, stackIndex) => (
                <div key={`stack-${index}-${stackIndex}`} className="stackEntry">
                  <div className="inline">
                    <label>
                      区分
                      <select
                        value={stack.category}
                        onChange={(e) =>
                          updateTechnologyStackField(
                            index,
                            stackIndex,
                            "category",
                            e.target.value
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
                          updateTechnologyStackField(index, stackIndex, "name", e.target.value)
                        }
                        placeholder="例: TypeScript"
                      />
                    </label>
                  </div>
                  <button
                    type="button"
                    className="ghost"
                    onClick={() => removeTechnologyStack(index, stackIndex)}
                  >
                    技術スタックを削除
                  </button>
                </div>
              ))}
              <button type="button" className="ghost" onClick={() => addTechnologyStack(index)}>
                技術スタックを追加
              </button>
            </div>

            <button type="button" className="ghost" onClick={() => removeExperience(index)}>
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
        <button type="button" onClick={onDownloadPdf} disabled={!resumeId || downloading}>
          {downloading ? "ダウンロード中..." : "PDF出力"}
        </button>
      </div>

      {resumeId && <p className="hint">保存ID: {resumeId}</p>}
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </form>
  );
}

function RirekishoForm() {
  const [form, setForm] = useState<RirekishoFormState>({
    postal_code: "",
    prefecture: "",
    address: "",
    email: "",
    phone: "",
    motivation: "",
    educations: [{ ...blankHistory }],
    work_histories: [{ ...blankHistory }]
  });
  const [rirekishoId, setRirekishoId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const saveButtonText = useMemo(() => {
    if (saving) {
      return "保存中...";
    }
    return rirekishoId ? "更新する" : "保存する";
  }, [rirekishoId, saving]);

  const onChangeField = (key: RirekishoTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const updateEducationField = (index: number, key: keyof RirekishoHistory, value: string) => {
    setForm((prev) => ({
      ...prev,
      educations: prev.educations.map((education, i) =>
        i === index ? { ...education, [key]: value } : education
      )
    }));
  };

  const updateWorkHistoryField = (
    index: number,
    key: keyof RirekishoHistory,
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
      const payload = buildRirekishoPayload(form);
      const saved = rirekishoId
        ? await updateRirekisho(rirekishoId, payload)
        : await createRirekisho(payload);

      setRirekishoId(saved.id);
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
    if (!rirekishoId) {
      return;
    }

    setDownloading(true);
    setError(null);
    setSuccess(null);

    try {
      await downloadRirekishoPdf(rirekishoId);
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

  return (
    <form onSubmit={onSubmit} className="form">
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
            <button type="button" className="ghost" onClick={() => removeEducation(index)}>
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
            <button type="button" className="ghost" onClick={() => removeWorkHistory(index)}>
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
        <button type="button" onClick={onDownloadPdf} disabled={!rirekishoId || downloading}>
          {downloading ? "ダウンロード中..." : "PDF出力"}
        </button>
      </div>

      {rirekishoId && <p className="hint">保存ID: {rirekishoId}</p>}
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </form>
  );
}

export default function App() {
  const [page, setPage] = useState<PageKey>("basic");

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
              className={`tabButton ${page === "rirekisho" ? "active" : ""}`}
              onClick={() => setPage("rirekisho")}
            >
              履歴書
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
          hidden={page !== "rirekisho"}
          className="pagePanel"
          aria-hidden={page !== "rirekisho"}
        >
          <RirekishoForm />
        </section>
      </main>
    </div>
  );
}
