import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createResume,
  downloadResumeMarkdown,
  downloadResumePdf,
  getLatestBasicInfo,
  getLatestResume,
  getResumePdfBlobUrl,
  updateResume,
} from "../../api";
import { buildResumePayload } from "../../payloadBuilders";
import type { ResumeFormState } from "../../payloadBuilders";
import type { ResumeHistory } from "../../types";
import { blankHistory } from "../../constants";
import type { ResumeTextFieldKey } from "../../formTypes";
import { usePrefectures } from "../../hooks/useMasterData";
import { usePdfActions } from "../../hooks/usePdfActions";
import shared from "../../styles/shared.module.css";
import { Combobox } from "./Combobox";
import { PdfPreviewModal } from "./PdfPreviewModal";
import styles from "./ResumeForm.module.css";

export function ResumeForm() {
  const [form, setForm] = useState<ResumeFormState>({
    gender: "",
    prefecture: "",
    address: "",
    address_furigana: "",
    email: "",
    phone: "",
    motivation: "",
    personal_preferences: "",
    educations: [{ ...blankHistory }],
    work_histories: [{ ...blankHistory }],
    photo: null,
  });
  const [resumeId, setresumeId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { items: prefectureOptions } = usePrefectures();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { downloading, previewUrl, closePreview, onDownloadPdf, onDownloadMarkdown, onPreviewPdf } =
    usePdfActions({
      downloadPdf: downloadResumePdf,
      downloadMarkdown: downloadResumeMarkdown,
      getPdfBlobUrl: getResumePdfBlobUrl,
    });

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const latest = await getLatestResume();
        if (!active) return;
        setresumeId(latest.id);
        setForm({
          gender: ((latest as Record<string, unknown>).gender as ResumeFormState["gender"]) ?? "",
          prefecture: latest.prefecture,
          address: latest.address,
          address_furigana: (latest as Record<string, unknown>).address_furigana as string ?? "",
          email: latest.email,
          phone: latest.phone,
          motivation: latest.motivation,
          personal_preferences: latest.personal_preferences ?? "",
          educations: latest.educations.length > 0 ? latest.educations : [{ ...blankHistory }],
          work_histories:
            latest.work_histories.length > 0 ? latest.work_histories : [{ ...blankHistory }],
          photo: latest.photo ?? null,
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
        i === index ? { ...education, [key]: value } : education,
      ),
    }));
  };

  const updateWorkHistoryField = (index: number, key: keyof ResumeHistory, value: string) => {
    setForm((prev) => ({
      ...prev,
      work_histories: prev.work_histories.map((workHistory, i) =>
        i === index ? { ...workHistory, [key]: value } : workHistory,
      ),
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
          : prev.educations.filter((_, i) => i !== index),
    }));
  };

  const addWorkHistory = () => {
    setForm((prev) => ({
      ...prev,
      work_histories: [...prev.work_histories, { ...blankHistory }],
    }));
  };

  const removeWorkHistory = (index: number) => {
    setForm((prev) => ({
      ...prev,
      work_histories:
        prev.work_histories.length === 1
          ? [{ ...blankHistory }]
          : prev.work_histories.filter((_, i) => i !== index),
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

      const payload = buildResumePayload(form);
      const saved = resumeId ? await updateResume(resumeId, payload) : await createResume(payload);

      setresumeId(saved.id);
      setSuccess("履歴書を保存しました。PDF出力できます。");
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
          <h1>履歴書</h1>
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
                onDownloadPdf(resumeId, setError, setSuccess, "履歴書PDFをダウンロードしました。")
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
              <h2>証明写真</h2>
          <div className={styles.photoUpload}>
            {form.photo ? (
              <img src={form.photo} alt="証明写真" className={styles.photoPreview} />
            ) : (
              <div className={styles.photoPlaceholder}>未選択</div>
            )}
            <div>
              <input type="file" accept="image/*" onChange={onPhotoChange} />
              {form.photo && (
                <button
                  type="button"
                  className="danger"
                  onClick={removePhoto}
                  style={{ marginTop: "0.5rem" }}
                >
                  写真を削除
                </button>
              )}
            </div>
          </div>
        </section>

        <section className={shared.section}>
          <div className={shared.inline}>
            <label>
              性別
              <select
                value={form.gender}
                onChange={(e) => onChangeField("gender", e.target.value)}
              >
                <option value="">未選択</option>
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </label>
          </div>
          <div className={shared.inline}>
            <label>
              <span className={shared.labelText}>都道府県<span className={shared.requiredBadge}>必須</span></span>
              <Combobox
                value={form.prefecture}
                onChange={(val) => onChangeField("prefecture", val)}
                options={prefectureOptions.map((pref) => pref.name)}
                placeholder="例: 東京都"
              />
            </label>
          </div>
          <label>
            住所ふりがな
            <input
              type="text"
              value={form.address_furigana}
              onChange={(e) => onChangeField("address_furigana", e.target.value)}
              placeholder="例: しぶやく じんなん"
            />
          </label>
          <label>
            <span className={shared.labelText}>住所<span className={shared.requiredBadge}>必須</span></span>
            <input
              type="text"
              value={form.address}
              onChange={(e) => onChangeField("address", e.target.value)}
              required
            />
          </label>
          <h3>連絡先</h3>
          <div className={shared.inline}>
            <label>
              <span className={shared.labelText}>電話番号<span className={shared.requiredBadge}>必須</span></span>
              <input
                type="text"
                value={form.phone}
                onChange={(e) => onChangeField("phone", e.target.value)}
                required
              />
            </label>
            <label>
              <span className={shared.labelText}>メールアドレス<span className={shared.requiredBadge}>必須</span></span>
              <input
                type="email"
                value={form.email}
                onChange={(e) => onChangeField("email", e.target.value)}
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
            />
          </label>
          <label>
            本人希望記入欄
            <textarea
              rows={4}
              value={form.personal_preferences}
              onChange={(e) => onChangeField("personal_preferences", e.target.value)}
            />
          </label>
        </section>

        <section className={shared.section}>
          <h2>学歴</h2>
          {form.educations.map((education, index) => (
            <div key={`education-${index}`} className={shared.entry}>
              <div className={shared.inline}>
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

        <section className={shared.section}>
          <h2>職歴</h2>
          {form.work_histories.map((workHistory, index) => (
            <div key={`work-${index}`} className={shared.entry}>
              <div className={shared.inline}>
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

          </div>
        </div>
      </form>
    </>
  );
}
