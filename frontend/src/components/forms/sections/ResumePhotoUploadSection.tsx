import { usePhotoUpload } from "../../../hooks/usePhotoUpload";
import styles from "../ResumeForm.module.css";
import shared from "../../../styles/shared.module.css";

/** ResumePhotoUploadSection のプロパティ型 */
type ResumePhotoUploadSectionProps = {
  /** 現在の写真データ（Base64 または null） */
  photo: string | null;
  /** 写真変更コールバック */
  onPhotoChange: (photo: string | null) => void;
};

/**
 * 履歴書の証明写真アップロードセクション。
 * usePhotoUpload を内包し、親は onPhotoChange のみ受け取る。
 */
export function ResumePhotoUploadSection({
  photo,
  onPhotoChange,
}: ResumePhotoUploadSectionProps) {
  /** 写真アップロードフック。選択した画像をリサイズして親へ通知する。 */
  const { handleFileChange } = usePhotoUpload((resized) => {
    onPhotoChange(resized);
  });

  /** 写真削除ハンドラ */
  const removePhoto = () => {
    onPhotoChange(null);
  };

  return (
    <section className={shared.section}>
      <h2>証明写真</h2>
      <div className={styles.photoUpload}>
        {photo ? (
          <img src={photo} alt="証明写真" className={styles.photoPreview} />
        ) : (
          <div className={styles.photoPlaceholder}>未選択</div>
        )}
        <div>
          <input type="file" accept="image/*" onChange={handleFileChange} />
          {photo && (
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
  );
}
