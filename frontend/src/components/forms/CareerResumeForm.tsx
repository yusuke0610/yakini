import { FormEvent, useMemo, useState } from "react";

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
import type { CareerProjectForm } from "../../payloadBuilders";
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
import { useProjectModalState } from "../../hooks/useProjectModalState";
import shared from "../../styles/shared.module.css";
import { ConfirmDialog } from "../ConfirmDialog";
import { LoadingOverlay } from "../LoadingOverlay";
import { MarkdownTextarea } from "./MarkdownTextarea";
import { PdfPreviewModal } from "./PdfPreviewModal";
import { ProjectModal } from "./ProjectModal";
import { CareerExperienceEditor } from "./CareerFormEditors/CareerExperienceEditor";

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

  /**
   * form の experiences からプロジェクトを取得するコールバック。
   * useProjectModalState に渡す。
   */
  const getProject = (
    expIndex: number,
    clientIndex: number,
    projIndex: number,
  ): CareerProjectForm | null => {
    return form.experiences[expIndex]?.clients[clientIndex]?.projects[projIndex] ?? null;
  };

  /**
   * モーダルで保存されたプロジェクトをフォームに反映するコールバック。
   * useProjectModalState に渡す。
   */
  const onProjectSave = (
    expIndex: number,
    clientIndex: number,
    projIndex: number | null,
    project: CareerProjectForm,
  ) => {
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
  };

  const {
    modalTarget,
    setModalTarget,
    modalProject,
    handleProjectSave,
    closeModal,
  } = useProjectModalState(getProject, onProjectSave);

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
    await save();
  };

  /** プロジェクトのサマリーテキストを生成する */
  const projectSummary = (proj: CareerProjectForm) => {
    const period = [proj.start_date, proj.is_current ? "現在" : proj.end_date]
      .filter(Boolean)
      .join(" 〜 ");
    return period || "";
  };

  /** モーダルを開くハンドラ。setModalTarget のラッパー。 */
  const handleOpenProjectModal = (
    expIndex: number,
    clientIndex: number,
    projIndex: number | null,
  ) => {
    setModalTarget({ expIndex, clientIndex, projIndex });
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
      {modalTarget && (
        <ProjectModal
          project={modalProject}
          onSave={handleProjectSave}
          onClose={closeModal}
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

            <section className={shared.section}>
              <h2>職務経歴</h2>
              {form.experiences.map((exp, expIndex) => (
                <CareerExperienceEditor
                  key={`exp-${expIndex}`}
                  exp={exp}
                  expIndex={expIndex}
                  onUpdateExperienceField={updateExperienceField}
                  onUpdateClientField={updateClientField}
                  onUpdateClientHasClient={updateClientHasClient}
                  onAddClient={addClient}
                  onRemoveClient={removeClient}
                  onRemoveProject={removeProject}
                  onOpenProjectModal={handleOpenProjectModal}
                  onRemoveExperience={removeExperience}
                  projectSummary={projectSummary}
                />
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
