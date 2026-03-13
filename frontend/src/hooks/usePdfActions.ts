import { useState } from "react";

export function usePdfActions({
  downloadPdf,
  downloadMarkdown,
  getPdfBlobUrl,
}: {
  downloadPdf: (id: string) => Promise<void>;
  downloadMarkdown: (id: string) => Promise<void>;
  getPdfBlobUrl: (id: string) => Promise<string>;
}) {
  const [downloading, setDownloading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const closePreview = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
  };

  const onDownloadPdf = async (
    id: string,
    setError: (msg: string | null) => void,
    setSuccess: (msg: string | null) => void,
    successMessage: string,
  ) => {
    setDownloading(true);
    setError(null);
    setSuccess(null);
    try {
      await downloadPdf(id);
      setSuccess(successMessage);
    } catch (e) {
      setError(e instanceof Error ? e.message : "PDFダウンロード中に不明なエラーが発生しました。");
    } finally {
      setDownloading(false);
    }
  };

  const onDownloadMarkdown = async (id: string, setError: (msg: string | null) => void) => {
    setError(null);
    try {
      await downloadMarkdown(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Markdownダウンロードに失敗しました。");
    }
  };

  const onPreviewPdf = async (id: string, setError: (msg: string | null) => void) => {
    setError(null);
    try {
      const url = await getPdfBlobUrl(id);
      setPreviewUrl(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "プレビューに失敗しました。");
    }
  };

  return { downloading, previewUrl, closePreview, onDownloadPdf, onDownloadMarkdown, onPreviewPdf };
}
