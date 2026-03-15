import { useEffect, useState } from "react";

import { getMasterData } from "../api";
import type { MasterDataItem } from "../types";

/** モジュールレベルのキャッシュ */
const cache = new Map<string, MasterDataItem[]>();

/** マスタデータを取得するフック */
export function useMasterData(category: string): { items: MasterDataItem[]; loading: boolean } {
  const [items, setItems] = useState<MasterDataItem[]>(cache.get(category) ?? []);
  const [loading, setLoading] = useState(!cache.has(category));

  useEffect(() => {
    if (cache.has(category)) {
      setItems(cache.get(category)!);
      setLoading(false);
      return;
    }

    let active = true;
    (async () => {
      try {
        const data = await getMasterData(category);
        cache.set(category, data);
        if (active) {
          setItems(data);
        }
      } catch {
        if (active) {
          setItems([]);
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
  }, [category]);

  return { items, loading };
}
