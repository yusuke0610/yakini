import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "../store";
import { clearCache, setCache, type FormCacheKey } from "../store/formCacheSlice";

type UseDocumentFormOptions<FormState, Payload, Response extends { id: string }> = {
  createInitialForm: () => FormState;
  loadLatest: () => Promise<Response>;
  createDocument: (payload: Payload) => Promise<Response>;
  updateDocument: (id: string, payload: Payload) => Promise<Response>;
  deleteDocument?: () => Promise<{ message: string }>;
  buildPayload: (form: FormState) => Payload;
  mapResponseToForm: (response: Response) => FormState;
  successMessage: string;
  beforeSave?: () => Promise<void>;
  /** 指定するとページ遷移してもフォーム状態が Redux ストアに保持される */
  cacheKey?: FormCacheKey;
};

export function useDocumentForm<FormState, Payload, Response extends { id: string }>({
  createInitialForm,
  loadLatest,
  createDocument,
  updateDocument,
  deleteDocument,
  buildPayload,
  mapResponseToForm,
  successMessage,
  beforeSave,
  cacheKey,
}: UseDocumentFormOptions<FormState, Payload, Response>) {
  const dispatch = useAppDispatch();
  const cached = useAppSelector((s) =>
    cacheKey ? s.formCache[cacheKey] : undefined,
  );

  const [form, setFormRaw] = useState<FormState>(() => {
    if (cached?.form) return cached.form as FormState;
    return createInitialForm();
  });
  const [documentId, setDocumentId] = useState<string | null>(
    cached?.documentId ?? null,
  );
  const [loading, setLoading] = useState(!cached);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  /** キャッシュキーを ref で保持（dispatch 時の最新値参照用） */
  const cacheKeyRef = useRef(cacheKey);
  cacheKeyRef.current = cacheKey;

  /** setForm のラッパー: Redux キャッシュも同時更新する */
  const setForm: React.Dispatch<React.SetStateAction<FormState>> = useCallback(
    (action) => {
      setFormRaw((prev) => {
        const next = typeof action === "function" ? (action as (prev: FormState) => FormState)(prev) : action;
        if (cacheKeyRef.current) {
          // documentId は現在の state から直接取れないため ref 不要、
          // setDocumentId は setForm と同タイミングで呼ばれるので後続の updateCache で上書きされる
          dispatch(
            setCache({
              key: cacheKeyRef.current,
              form: next,
              documentId: null, // 後で updateCache で正確な値に上書き
            }),
          );
        }
        return next;
      });
    },
    [dispatch],
  );

  /** フォームと documentId を同時に Redux キャッシュに反映する */
  const updateCache = useCallback(
    (formData: FormState, docId: string | null) => {
      if (cacheKeyRef.current) {
        dispatch(
          setCache({ key: cacheKeyRef.current, form: formData, documentId: docId }),
        );
      }
    },
    [dispatch],
  );

  useEffect(() => {
    // キャッシュが既にある場合は API ロードをスキップ
    if (cached) return;

    let active = true;
    setLoading(true);

    (async () => {
      try {
        const latest = await loadLatest();
        if (!active) return;
        setDocumentId(latest.id);
        const mapped = mapResponseToForm(latest);
        setFormRaw(mapped);
        updateCache(mapped, latest.id);
      } catch {
        if (!active) return;
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => {
      active = false;
    };
    // cached を依存配列に含めないことで、キャッシュ更新のたびに再 fetch しない
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadLatest, mapResponseToForm, updateCache]);

  const saveButtonText = useMemo(() => {
    if (saving) return "保存中...";
    return documentId ? "更新する" : "保存する";
  }, [documentId, saving]);

  const save = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      if (beforeSave) await beforeSave();
      const payload = buildPayload(form);
      const saved = documentId
        ? await updateDocument(documentId, payload)
        : await createDocument(payload);
      const mapped = mapResponseToForm(saved);
      setDocumentId(saved.id);
      setFormRaw(mapped);
      updateCache(mapped, saved.id);
      setSuccess(successMessage);
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

  const deleteDoc = async () => {
    if (!deleteDocument || !documentId) return;
    setDeleting(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await deleteDocument();
      setDocumentId(null);
      const initial = createInitialForm();
      setFormRaw(initial);
      if (cacheKeyRef.current) {
        dispatch(clearCache(cacheKeyRef.current));
      }
      setSuccess(result.message);
    } catch (deleteError) {
      const message =
        deleteError instanceof Error
          ? deleteError.message
          : "削除中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setDeleting(false);
    }
  };

  return {
    form,
    setForm,
    documentId,
    loading,
    saving,
    deleting,
    error,
    success,
    setError,
    setSuccess,
    save,
    deleteDoc,
    saveButtonText,
  };
}
