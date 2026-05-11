import { FormEvent, useState } from "react";

import {
  createCareerResume,
  deleteCareerResume,
  downloadCareerResumeMarkdown,
  downloadCareerResumePdf,
  getCareerResumePdfBlobUrl,
  getLatestCareerResume,
  updateCareerResume,
} from "../../api";
import { createInitialCareerForm, mapCareerResumeToForm } from "../../formMappers";
import { useDocumentForm } from "../../hooks/useDocumentForm";
import { buildCareerPayload } from "../../payloadBuilders";
import type { CareerTextFieldKey } from "../../formTypes";
import { useQualifications, useTechnologyStacks } from "../../hooks/useMasterData";
import { usePdfActions } from "../../hooks/usePdfActions";
import type { ResumeQualification } from "../../types";
import { blankResumeQualification } from "../../constants";
import shared from "../../styles/shared.module.css";
import { ConfirmDialog } from "../ConfirmDialog";
import { Skeleton } from "../ui/Skeleton";
import { Combobox } from "./Combobox";
import { MarkdownTextarea } from "./MarkdownTextarea";
import { PdfPreviewModal } from "./PdfPreviewModal";
import { CareerExperienceSection } from "./sections/CareerExperienceSection";

export function CareerResumeForm() {
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
    createInitialForm: createInitialCareerForm,
    loadLatest: getLatestCareerResume,
    createDocument: createCareerResume,
    updateDocument: updateCareerResume,
    deleteDocument: deleteCareerResume,
    buildPayload: buildCareerPayload,
    mapResponseToForm: mapCareerResumeToForm,
    successMessage: "職務経歴書を保存しました。PDF出力できます。",
    cacheKey: "career",
  });

  const { items: techStackOptions, loading: techLoading } = useTechnologyStacks();
  const { items: qualificationOptions, loading: qualLoading } = useQualifications();
  const qualificationNames = qualificationOptions.map((item) => item.name);

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
    downloadPdf: downloadCareerResumePdf,
    downloadMarkdown: downloadCareerResumeMarkdown,
    getPdfBlobUrl: getCareerResumePdfBlobUrl,
  });

  /** PDF アクションまたはフォーム保存のエラー・成功メッセージを統合して表示する */
  const error = pdfError ?? formError;
  const success = pdfSuccess ?? formSuccess;

  /** フォームデータ・技術スタック・資格の3つが揃ってから送信可能 */
  const canSubmit = !loading && !techLoading && !qualLoading;

  const onChangeField = (key: CareerTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  /** 資格フィールド変更ハンドラ */
  const updateQualificationField = (
    index: number,
    key: keyof ResumeQualification,
    value: string,
  ) => {
    setForm((prev) => ({
      ...prev,
      qualifications: prev.qualifications.map((qualification, i) =>
        i === index ? { ...qualification, [key]: value } : qualification,
      ),
    }));
  };

  /** 資格追加ハンドラ */
  const addQualification = () => {
    setForm((prev) => ({
      ...prev,
      qualifications: [...prev.qualifications, { ...blankResumeQualification }],
    }));
  };

  /** 資格削除ハンドラ */
  const removeQualification = (index: number) => {
    setForm((prev) => ({
      ...prev,
      qualifications:
        prev.qualifications.length === 1
          ? [{ ...blankResumeQualification }]
          : prev.qualifications.filter((_, i) => i !== index),
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

  return (
    <>
      {showDeleteConfirm && (
        <ConfirmDialog
          message="職務経歴書のデータを全て削除します。この操作は取り消せません。本当に削除しますか？"
          confirmLabel="削除する"
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
          confirming={deleting}
        />
      )}
      {previewUrl && <PdfPreviewModal previewUrl={previewUrl} onClose={closePreview} />}
      <form onSubmit={onSubmit}>
        <div className={shared.pageHeader}>
          <h1>職務経歴書</h1>
          <div className={shared.pageHeaderActions}>
            <button type="submit" className="primary" disabled={!canSubmit || saving}>
              {saveButtonText}
            </button>
            <button
              type="button"
              onClick={() => resumeId && onPreviewPdf(resumeId)}
              disabled={!resumeId || loading}
            >
              プレビュー
            </button>
            <button
              type="button"
              onClick={() =>
                resumeId &&
                onDownloadPdf(resumeId, "職務経歴書PDFをダウンロードしました。")
              }
              disabled={!resumeId || downloading || loading}
            >
              {downloading ? "ダウンロード中..." : "PDF出力"}
            </button>
            <button
              type="button"
              onClick={() => resumeId && onDownloadMarkdown(resumeId)}
              disabled={!resumeId || loading}
            >
              Markdown出力
            </button>
            <button
              type="button"
              className="danger"
              onClick={() => setShowDeleteConfirm(true)}
              disabled={!resumeId || loading}
            >
              データを削除
            </button>
          </div>
        </div>

        <div className={shared.pageBody}>
          <div className={shared.form}>
            {error && <p className={shared.error}>{error}</p>}
            {success && <p className={shared.success}>{success}</p>}

            {/* 基本情報: 氏名・職務要約 */}
            <section className={shared.section}>
              <label>
                <span className={shared.labelText}>
                  氏名<span className={shared.requiredBadge}>必須</span>
                </span>
                {loading ? (
                  <Skeleton height="38px" />
                ) : (
                  <input
                    type="text"
                    value={form.full_name}
                    onChange={(e) => onChangeField("full_name", e.target.value)}
                    placeholder="例: 山田 太郎"
                    required
                  />
                )}
              </label>
              {loading ? (
                <Skeleton height="110px" />
              ) : (
                <MarkdownTextarea
                  label="職務要約"
                  value={form.career_summary}
                  onChange={(v) => onChangeField("career_summary", v)}
                  rows={4}
                  required
                />
              )}
            </section>

            {/* 職務経歴セクション */}
            {loading ? (
              <section className={shared.section}>
                <Skeleton height="20px" width="80px" borderRadius="4px" />
                <div className={shared.entry} style={{ marginTop: "0.8rem" }}>
                  <Skeleton height="120px" />
                </div>
                <div className={shared.entry}>
                  <Skeleton height="120px" />
                </div>
              </section>
            ) : (
              <CareerExperienceSection
                experiences={form.experiences}
                setForm={setForm}
                techStackOptions={techStackOptions}
              />
            )}

            {/* 資格セクション */}
            <section className={shared.section}>
              <h2>資格</h2>
              {loading ? (
                <div className={shared.entry}>
                  <Skeleton height="56px" />
                </div>
              ) : (
                <>
                  {form.qualifications.map((qualification, index) => (
                    <div key={`qualification-${index}`} className={shared.entry}>
                      <div className={shared.inline}>
                        <label>
                          資格名 ※プルダウンにないものはテキストで入力できます。
                          <Combobox
                            value={qualification.name}
                            onChange={(val) => updateQualificationField(index, "name", val)}
                            options={qualificationNames}
                            placeholder="例: 基本情報技術者試験"
                            allowCustom
                          />
                        </label>
                        <label>
                          取得日
                          <input
                            type="date"
                            value={qualification.acquired_date}
                            onChange={(e) => updateQualificationField(index, "acquired_date", e.target.value)}
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
                </>
              )}
            </section>

            {/* 自己PR */}
            <section className={shared.section}>
              {loading ? (
                <Skeleton height="110px" />
              ) : (
                <MarkdownTextarea
                  label="自己PR"
                  value={form.self_pr}
                  onChange={(v) => onChangeField("self_pr", v)}
                  rows={4}
                  required
                />
              )}
            </section>
          </div>
        </div>
      </form>
    </>
  );
}
