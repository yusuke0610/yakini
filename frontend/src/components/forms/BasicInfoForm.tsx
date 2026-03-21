import { FormEvent } from "react";

import { createBasicInfo, getLatestBasicInfo, updateBasicInfo } from "../../api";
import { createInitialBasicForm, mapBasicInfoToForm } from "../../formMappers";
import { useDocumentForm } from "../../hooks/useDocumentForm";
import { buildBasicPayload } from "../../payloadBuilders";
import type { BasicQualification } from "../../types";
import { blankBasicQualification } from "../../constants";
import type { BasicTextFieldKey } from "../../formTypes";
import { useQualifications } from "../../hooks/useMasterData";
import shared from "../../styles/shared.module.css";
import { LoadingOverlay } from "../LoadingOverlay";
import { Combobox } from "./Combobox";

export function BasicInfoForm() {
  const { items: qualificationOptions } = useQualifications();
  const qualificationNames = qualificationOptions.map((item) => item.name);
  const {
    form,
    setForm,
    loading,
    saving,
    error,
    success,
    save,
    saveButtonText,
  } = useDocumentForm({
    createInitialForm: createInitialBasicForm,
    loadLatest: getLatestBasicInfo,
    createDocument: createBasicInfo,
    updateDocument: updateBasicInfo,
    buildPayload: buildBasicPayload,
    mapResponseToForm: mapBasicInfoToForm,
    successMessage: "基本情報を保存しました。",
  });

  const onChangeField = (key: BasicTextFieldKey, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const updateQualificationField = (
    index: number,
    key: keyof BasicQualification,
    value: string,
  ) => {
    setForm((prev) => ({
      ...prev,
      qualifications: prev.qualifications.map((qualification, i) =>
        i === index ? { ...qualification, [key]: value } : qualification,
      ),
    }));
  };

  const addQualification = () => {
    setForm((prev) => ({
      ...prev,
      qualifications: [...prev.qualifications, { ...blankBasicQualification }],
    }));
  };

  const removeQualification = (index: number) => {
    setForm((prev) => ({
      ...prev,
      qualifications:
        prev.qualifications.length === 1
          ? [{ ...blankBasicQualification }]
          : prev.qualifications.filter((_, i) => i !== index),
    }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await save();
  };

  if (loading) return <LoadingOverlay />;

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className={shared.pageHeader}>
        <h1>基本情報</h1>
        <div className={shared.pageHeaderActions}>
          <button type="submit" className="primary" disabled={saving}>
            {saveButtonText}
          </button>
        </div>
      </div>

      <div className={shared.pageBody}>
        <div className={shared.form}>
          {error && <p className={shared.error}>{error}</p>}
          {success && <p className={shared.success}>{success}</p>}

          <section className={shared.section}>
            <div className={shared.inline}>
              <label>
                <span className={shared.labelText}>氏名<span className={shared.requiredBadge}>必須</span></span>
                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) => onChangeField("full_name", e.target.value)}
                  required
                />
              </label>
              <label>
                <span className={shared.labelText}>ふりがな<span className={shared.requiredBadge}>必須</span></span>
                <input
                  type="text"
                  value={form.name_furigana}
                  onChange={(e) => onChangeField("name_furigana", e.target.value)}
                  placeholder="例: やまだ たろう"
                  pattern="^[ぁ-ゖー\s　]+$"
                  title="ひらがなで入力してください"
                  required
                />
              </label>
            </div>
            <label>
              <span className={shared.labelText}>記載日<span className={shared.requiredBadge}>必須</span></span>
              <input
                type="date"
                value={form.record_date}
                onChange={(e) => onChangeField("record_date", e.target.value)}
                required
              />
            </label>
          </section>

          <section className={shared.section}>
            <h2>資格</h2>
            {form.qualifications.map((qualification, index) => (
              <div key={`basic-qualification-${index}`} className={shared.entry}>
                <div className={shared.inline}>
                  <label>
                    資格名
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
          </section>

        </div>
      </div>
    </form>
  );
}
