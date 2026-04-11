import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

/** フォームキャッシュのキー。各フォームページに対応。 */
export type FormCacheKey = "career";

interface FormCacheEntry {
  /** フォーム状態（型は各フォームに依存するため unknown） */
  form: unknown;
  /** 保存済みドキュメント ID（未保存なら null） */
  documentId: string | null;
}

type FormCacheState = Record<string, FormCacheEntry | undefined>;

const formCacheSlice = createSlice({
  name: "formCache",
  initialState: {} as FormCacheState,
  reducers: {
    setCache(
      state,
      action: PayloadAction<{
        key: FormCacheKey;
        form: unknown;
        documentId: string | null;
      }>,
    ) {
      const { key, form, documentId } = action.payload;
      state[key] = { form, documentId };
    },
    clearCache(state, action: PayloadAction<FormCacheKey>) {
      delete state[action.payload];
    },
  },
});

export const { setCache, clearCache } = formCacheSlice.actions;
export default formCacheSlice.reducer;
