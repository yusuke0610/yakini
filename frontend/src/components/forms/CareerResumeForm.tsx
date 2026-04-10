import { FormEvent, useState } from "react";

import {
  assertBasicInfoReady,
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
import { useTechnologyStacks } from "../../hooks/useMasterData";
import { usePdfActions } from "../../hooks/usePdfActions";
import shared from "../../styles/shared.module.css";
import { ConfirmDialog } from "../ConfirmDialog";
import { LoadingOverlay } from "../LoadingOverlay";
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
    beforeSave: assertBasicInfoReady,
    cacheKey: "career",
  });

  const { items: techStackOptions } = useTechnologyStacks();

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

  const onChangeField = (key: CareerTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
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
                onDownloadPdf(resumeId, "職務経歴書PDFをダウンロードしました。")
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

            {/* 職務経歴セクション: experiences 操作・モーダル管理を委譲 */}
            <CareerExperienceSection
              experiences={form.experiences}
              setForm={setForm}
              techStackOptions={techStackOptions}
            />
          </div>
        </div>
      </form>
    </>
  );
}
