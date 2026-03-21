import { useEffect, useMemo, useState } from "react";

type UseDocumentFormOptions<FormState, Payload, Response extends { id: string }> = {
  createInitialForm: () => FormState;
  loadLatest: () => Promise<Response>;
  createDocument: (payload: Payload) => Promise<Response>;
  updateDocument: (id: string, payload: Payload) => Promise<Response>;
  buildPayload: (form: FormState) => Payload;
  mapResponseToForm: (response: Response) => FormState;
  successMessage: string;
  beforeSave?: () => Promise<void>;
};

export function useDocumentForm<FormState, Payload, Response extends { id: string }>({
  createInitialForm,
  loadLatest,
  createDocument,
  updateDocument,
  buildPayload,
  mapResponseToForm,
  successMessage,
  beforeSave,
}: UseDocumentFormOptions<FormState, Payload, Response>) {
  const [form, setForm] = useState<FormState>(() => createInitialForm());
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);

    (async () => {
      try {
        const latest = await loadLatest();
        if (!active) {
          return;
        }
        setDocumentId(latest.id);
        setForm(mapResponseToForm(latest));
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
  }, [loadLatest, mapResponseToForm]);

  const saveButtonText = useMemo(() => {
    if (saving) {
      return "保存中...";
    }
    return documentId ? "更新する" : "保存する";
  }, [documentId, saving]);

  const save = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      if (beforeSave) {
        await beforeSave();
      }
      const payload = buildPayload(form);
      const saved = documentId
        ? await updateDocument(documentId, payload)
        : await createDocument(payload);
      setDocumentId(saved.id);
      setForm(mapResponseToForm(saved));
      setSuccess(successMessage);
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "保存中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return {
    form,
    setForm,
    documentId,
    loading,
    saving,
    error,
    success,
    setError,
    setSuccess,
    save,
    saveButtonText,
  };
}
