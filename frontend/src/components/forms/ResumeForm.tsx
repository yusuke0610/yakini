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
import { usePdfActions } from "../../hooks/usePdfActions";
import { PdfPreviewModal } from "./PdfPreviewModal";

export function ResumeForm() {
  const [form, setForm] = useState<ResumeFormState>({
    postal_code: "",
    prefecture: "",
    address: "",
    email: "",
    phone: "",
    motivation: "",
    personal_preferences: "",
    educations: [{ ...blankHistory }],
    work_histories: [{ ...blankHistory }],
    photo: null,
  });
  const [ResumeId, setResumeId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
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
        setResumeId(latest.id);
        setForm({
          postal_code: latest.postal_code,
          prefecture: latest.prefecture,
          address: latest.address,
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
      const saved = ResumeId ? await updateResume(ResumeId, payload) : await createResume(payload);

      setResumeId(saved.id);
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
        <div className="pageHeader">
          <h1>履歴書</h1>
          <div className="pageHeaderActions">
            <button type="submit" disabled={saving}>
              {saveButtonText}
            </button>
            <button
              type="button"
              onClick={() => ResumeId && onPreviewPdf(ResumeId, setError)}
              disabled={!ResumeId}
            >
              プレビュー
            </button>
            <button
              type="button"
              onClick={() =>
                ResumeId &&
                onDownloadPdf(ResumeId, setError, setSuccess, "履歴書PDFをダウンロードしました。")
              }
              disabled={!ResumeId || downloading}
            >
              {downloading ? "ダウンロード中..." : "PDF出力"}
            </button>
            <button
              type="button"
              onClick={() => ResumeId && onDownloadMarkdown(ResumeId, setError)}
              disabled={!ResumeId}
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

        <section className="section">
          <div className="inline">
            <label>
              <span className="labelText">郵便番号<span className="requiredBadge">必須</span></span>
              <input
                type="text"
                value={form.postal_code}
                onChange={(e) => onChangeField("postal_code", e.target.value)}
                placeholder="例: 150-0001"
                required
              />
            </label>
            <label>
              <span className="labelText">都道府県<span className="requiredBadge">必須</span></span>
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
            <span className="labelText">住所<span className="requiredBadge">必須</span></span>
            <input
              type="text"
              value={form.address}
              onChange={(e) => onChangeField("address", e.target.value)}
              required
            />
          </label>
          <div className="inline">
            <label>
              <span className="labelText">メールアドレス<span className="requiredBadge">必須</span></span>
              <input
                type="email"
                value={form.email}
                onChange={(e) => onChangeField("email", e.target.value)}
                required
              />
            </label>
            <label>
              <span className="labelText">電話番号<span className="requiredBadge">必須</span></span>
              <input
                type="text"
                value={form.phone}
                onChange={(e) => onChangeField("phone", e.target.value)}
                required
              />
            </label>
          </div>
          <label>
            <span className="labelText">志望動機<span className="requiredBadge">必須</span></span>
            <textarea
              rows={4}
              value={form.motivation}
              onChange={(e) => onChangeField("motivation", e.target.value)}
              required
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

            {ResumeId && <p className="hint">保存ID: {ResumeId}</p>}
          </div>
        </div>
      </form>
    </>
  );
}
