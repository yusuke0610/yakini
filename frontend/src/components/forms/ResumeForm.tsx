import { FormEvent, useState } from "react";

import {
  assertBasicInfoReady,
  createResume,
  deleteResume,
  downloadResumeMarkdown,
  downloadResumePdf,
  getLatestResume,
  getResumePdfBlobUrl,
  updateResume,
} from "../../api";
import { createInitialResumeForm, mapResumeToForm } from "../../formMappers";
import { useDocumentForm } from "../../hooks/useDocumentForm";
import { buildResumePayload } from "../../payloadBuilders";
import type { ResumeTextFieldKey } from "../../formTypes";
import { usePrefectures } from "../../hooks/useMasterData";
import { usePdfActions } from "../../hooks/usePdfActions";
import shared from "../../styles/shared.module.css";
import { ConfirmDialog } from "../ConfirmDialog";
import { LoadingOverlay } from "../LoadingOverlay";
import { Combobox } from "./Combobox";
import { MarkdownTextarea } from "./MarkdownTextarea";
import { PdfPreviewModal } from "./PdfPreviewModal";
import { ResumePhotoUploadSection } from "./sections/ResumePhotoUploadSection";
import { ResumeEducationSection } from "./sections/ResumeEducationSection";
import { ResumeWorkHistorySection } from "./sections/ResumeWorkHistorySection";
import type { ResumeHistory } from "../../types";
import { blankHistory } from "../../constants";

export function ResumeForm() {
  const { items: prefectureOptions } = usePrefectures();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const {
    form,
    setForm,
    documentId: resumeId,
    loading,
    saving,
    deleting,
    error: formError,
    success: formSuccess,
    save,
    deleteDoc,
    saveButtonText,
  } = useDocumentForm({
    createInitialForm: createInitialResumeForm,
    loadLatest: getLatestResume,
    createDocument: createResume,
    updateDocument: updateResume,
    deleteDocument: deleteResume,
    buildPayload: buildResumePayload,
    mapResponseToForm: mapResumeToForm,
    successMessage: "履歴書を保存しました。PDF出力できます。",
    beforeSave: assertBasicInfoReady,
    cacheKey: "resume",
  });

  const {
    downloading,
    previewUrl,
    closePreview,
    onDownloadPdf,
    onDownloadMarkdown,
    onPreviewPdf,
    error: pdfError,
    success: pdfSuccess,
  } = usePdfActions({
    downloadPdf: downloadResumePdf,
    downloadMarkdown: downloadResumeMarkdown,
    getPdfBlobUrl: getResumePdfBlobUrl,
  });

  /** PDF アクションまたはフォーム保存のエラー・成功メッセージを統合して表示する */
  const error = pdfError ?? formError;
  const success = pdfSuccess ?? formSuccess;

  const onChangeField = (key: ResumeTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  /** 写真変更ハンドラ。null の場合は写真削除とみなす。 */
  const onPhotoChange = (photo: string | null) => {
    setForm((prev) => ({ ...prev, photo }));
  };

  /** 学歴フィールド変更ハンドラ */
  const updateEducationField = (index: number, key: keyof ResumeHistory, value: string) => {
    setForm((prev) => ({
      ...prev,
      educations: prev.educations.map((education, i) =>
        i === index ? { ...education, [key]: value } : education,
      ),
    }));
  };

  /** 学歴追加ハンドラ */
  const addEducation = () => {
    setForm((prev) => ({ ...prev, educations: [...prev.educations, { ...blankHistory }] }));
  };

  /** 学歴削除ハンドラ */
  const removeEducation = (index: number) => {
    setForm((prev) => ({
      ...prev,
      educations:
        prev.educations.length === 1
          ? [{ ...blankHistory }]
          : prev.educations.filter((_, i) => i !== index),
    }));
  };

  /** 職歴フィールド変更ハンドラ */
  const updateWorkHistoryField = (index: number, key: keyof ResumeHistory, value: string) => {
    setForm((prev) => ({
      ...prev,
      work_histories: prev.work_histories.map((workHistory, i) =>
        i === index ? { ...workHistory, [key]: value } : workHistory,
      ),
    }));
  };

  /** 職歴追加ハンドラ */
  const addWorkHistory = () => {
    setForm((prev) => ({
      ...prev,
      work_histories: [...prev.work_histories, { ...blankHistory }],
    }));
  };

  /** 職歴削除ハンドラ */
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
    await save();
  };

  const handleDelete = async () => {
    await deleteDoc();
    setShowDeleteConfirm(false);
  };

  if (loading) return <LoadingOverlay />;

  return (
    <>
      {showDeleteConfirm && (
        <ConfirmDialog
          message="履歴書のデータを全て削除します。この操作は取り消せません。本当に削除しますか？"
          confirmLabel="削除する"
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
          confirming={deleting}
        />
      )}
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
              onClick={() => resumeId && onPreviewPdf(resumeId)}
              disabled={!resumeId}
            >
              プレビュー
            </button>
            <button
              type="button"
              onClick={() =>
                resumeId &&
                onDownloadPdf(resumeId, "履歴書PDFをダウンロードしました。")
              }
              disabled={!resumeId || downloading}
            >
              {downloading ? "ダウンロード中..." : "PDF出力"}
            </button>
            <button
              type="button"
              onClick={() => resumeId && onDownloadMarkdown(resumeId)}
              disabled={!resumeId}
            >
              Markdown出力
            </button>
            <button
              type="button"
              className="danger"
              onClick={() => setShowDeleteConfirm(true)}
              disabled={!resumeId}
            >
              データを削除
            </button>
          </div>
        </div>

        <div className={shared.pageBody}>
          <div className={shared.form}>
            {error && <p className={shared.error}>{error}</p>}
            {success && <p className={shared.success}>{success}</p>}

            {/* 証明写真セクション */}
            <ResumePhotoUploadSection
              photo={form.photo}
              onPhotoChange={onPhotoChange}
            />

            <section className={shared.section}>
              <div className={shared.inline}>
                <label>
                  <span className={shared.labelText}>性別<span className={shared.requiredBadge}>必須</span></span>
                  <select
                    value={form.gender}
                    onChange={(e) => onChangeField("gender", e.target.value)}
                    required
                  >
                    <option value="">未選択</option>
                    <option value="male">男</option>
                    <option value="female">女</option>
                  </select>
                </label>
                <label>
                  <span className={shared.labelText}>生年月日<span className={shared.requiredBadge}>必須</span></span>
                  <input
                    type="date"
                    value={form.birthday}
                    onChange={(e) => onChangeField("birthday", e.target.value)}
                    required
                  />
                </label>
                <label>
                  <span className={shared.labelText}>都道府県<span className={shared.requiredBadge}>必須</span></span>
                  <Combobox
                    value={form.prefecture}
                    onChange={(val) => onChangeField("prefecture", val)}
                    options={prefectureOptions.map((pref) => pref.name)}
                    placeholder="例: 東京都"
                  />
                </label>
                <label>
                  <span className={shared.labelText}>郵便番号<span className={shared.requiredBadge}>必須</span></span>
                  <input
                    type="text"
                    value={form.postal_code}
                    onChange={(e) => onChangeField("postal_code", e.target.value)}
                    placeholder="例: 150-0041"
                    required
                  />
                </label>
              </div>
              <label>
                <span className={shared.labelText}>住所ふりがな<span className={shared.requiredBadge}>必須</span></span>
                <input
                  type="text"
                  value={form.address_furigana}
                  onChange={(e) => onChangeField("address_furigana", e.target.value)}
                  placeholder="例: しぶやく じんなん"
                  pattern="^[ぁ-ゖー\s　]+$"
                  title="ひらがなで入力してください"
                  required
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
              <MarkdownTextarea
                label="志望動機"
                value={form.motivation}
                onChange={(v) => onChangeField("motivation", v)}
                rows={4}
              />
              <MarkdownTextarea
                label="本人希望記入欄"
                value={form.personal_preferences}
                onChange={(v) => onChangeField("personal_preferences", v)}
                rows={4}
              />
            </section>

            {/* 学歴セクション */}
            <ResumeEducationSection
              educations={form.educations}
              onFieldChange={updateEducationField}
              onAdd={addEducation}
              onRemove={removeEducation}
            />

            {/* 職歴セクション */}
            <ResumeWorkHistorySection
              workHistories={form.work_histories}
              onFieldChange={updateWorkHistoryField}
              onAdd={addWorkHistory}
              onRemove={removeWorkHistory}
            />
          </div>
        </div>
      </form>
    </>
  );
}
