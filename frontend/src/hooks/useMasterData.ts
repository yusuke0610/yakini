import { useEffect, useState } from "react";

import { getPrefectures, getQualifications, getTechnologyStacks } from "../api";
import type { MasterItem, TechStackMasterItem } from "../types";

/** モジュールレベルのキャッシュ */
let qualificationsCache: MasterItem[] | null = null;
let techStacksCache: TechStackMasterItem[] | null = null;
let prefecturesCache: MasterItem[] | null = null;

/** 資格マスタを取得するフック */
export function useQualifications(): { items: MasterItem[]; loading: boolean } {
  const [items, setItems] = useState<MasterItem[]>(qualificationsCache ?? []);
  const [loading, setLoading] = useState(qualificationsCache === null);

  useEffect(() => {
    if (qualificationsCache !== null) {
      setItems(qualificationsCache);
      setLoading(false);
      return;
    }

    let active = true;
    (async () => {
      try {
        const data = await getQualifications();
        qualificationsCache = data;
        if (active) setItems(data);
      } catch {
        if (active) setItems([]);
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => { active = false; };
  }, []);

  return { items, loading };
}

/** 技術スタックマスタを取得するフック */
export function useTechnologyStacks(): { items: TechStackMasterItem[]; loading: boolean } {
  const [items, setItems] = useState<TechStackMasterItem[]>(techStacksCache ?? []);
  const [loading, setLoading] = useState(techStacksCache === null);

  useEffect(() => {
    if (techStacksCache !== null) {
      setItems(techStacksCache);
      setLoading(false);
      return;
    }

    let active = true;
    (async () => {
      try {
        const data = await getTechnologyStacks();
        techStacksCache = data;
        if (active) setItems(data);
      } catch {
        if (active) setItems([]);
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => { active = false; };
  }, []);

  return { items, loading };
}

/** 都道府県マスタを取得するフック */
export function usePrefectures(): { items: MasterItem[]; loading: boolean } {
  const [items, setItems] = useState<MasterItem[]>(prefecturesCache ?? []);
  const [loading, setLoading] = useState(prefecturesCache === null);

  useEffect(() => {
    if (prefecturesCache !== null) {
      setItems(prefecturesCache);
      setLoading(false);
      return;
    }

    let active = true;
    (async () => {
      try {
        const data = await getPrefectures();
        prefecturesCache = data;
        if (active) setItems(data);
      } catch {
        if (active) setItems([]);
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => { active = false; };
  }, []);

  return { items, loading };
}
