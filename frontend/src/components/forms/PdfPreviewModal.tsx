export function PdfPreviewModal({
  previewUrl,
  onClose,
}: {
  previewUrl: string;
  onClose: () => void;
}) {
  return (
    <div className="previewOverlay" onClick={onClose}>
      <div className="previewModal" onClick={(e) => e.stopPropagation()}>
        <div className="previewHeader">
          <span>PDFプレビュー</span>
          <button type="button" onClick={onClose}>
            閉じる
          </button>
        </div>
        <iframe src={previewUrl} className="previewFrame" title="PDF Preview" />
      </div>
    </div>
  );
}
