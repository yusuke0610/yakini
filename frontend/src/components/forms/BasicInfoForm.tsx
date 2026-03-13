import { FormEvent, useEffect, useMemo, useState } from "react";

import { createBasicInfo, getLatestBasicInfo, updateBasicInfo } from "../../api";
import { buildBasicPayload } from "../../payloadBuilders";
import type { BasicFormState } from "../../payloadBuilders";
import type { BasicQualification } from "../../types";
import { blankBasicQualification } from "../../constants";
import type { BasicTextFieldKey } from "../../formTypes";

export function BasicInfoForm() {
  const [form, setForm] = useState<BasicFormState>({
    full_name: "",
    record_date: "",
    qualifications: [{ ...blankBasicQualification }],
  });
  const [basicInfoId, setBasicInfoId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const latest = await getLatestBasicInfo();
        if (!active) {
          return;
        }
        setBasicInfoId(latest.id);
        setForm({
          full_name: latest.full_name,
          record_date: latest.record_date,
          qualifications:
            latest.qualifications.length > 0
              ? latest.qualifications
              : [{ ...blankBasicQualification }],
        });
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
  }, []);

  const saveButtonText = useMemo(() => {
    if (saving) {
      return "保存中...";
    }
    return basicInfoId ? "更新する" : "保存する";
  }, [basicInfoId, saving]);

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
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = buildBasicPayload(form);
      const saved = basicInfoId
        ? await updateBasicInfo(basicInfoId, payload)
        : await createBasicInfo(payload);
      setBasicInfoId(saved.id);
      setSuccess("基本情報を保存しました。");
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "保存中に不明なエラーが発生しました。";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="hint">基本情報を読み込み中です...</p>;
  }

  return (
    <form onSubmit={onSubmit}>
      <div className="pageHeader">
        <h1>基本情報</h1>
        <div className="pageHeaderActions">
          <button type="submit" disabled={saving}>
            {saveButtonText}
          </button>
        </div>
      </div>

      <div className="pageBody">
        <div className="form">
          {error && <p className="error">{error}</p>}
          {success && <p className="success">{success}</p>}

          <section className="section">
            <label>
              <span className="labelText">氏名<span className="requiredBadge">必須</span></span>
              <input
                type="text"
                value={form.full_name}
                onChange={(e) => onChangeField("full_name", e.target.value)}
                required
              />
            </label>
            <label>
              <span className="labelText">記載日<span className="requiredBadge">必須</span></span>
              <input
                type="date"
                value={form.record_date}
                onChange={(e) => onChangeField("record_date", e.target.value)}
                required
              />
            </label>
          </section>

          <section className="section">
            <h2>資格</h2>
            {form.qualifications.map((qualification, index) => (
              <div key={`basic-qualification-${index}`} className="entry">
                <div className="inline">
                  <label>
                    資格名
                    <input
                      type="text"
                      value={qualification.name}
                      onChange={(e) => updateQualificationField(index, "name", e.target.value)}
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

          {basicInfoId && <p className="hint">保存ID: {basicInfoId}</p>}
        </div>
      </div>
    </form>
  );
}
