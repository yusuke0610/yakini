import { useState, useEffect } from "react";
import { useTaskPolling } from "../useTaskPolling";

/** 分析ページのフェーズ型 */
export type AsyncAnalysisPhase = "loading-cache" | "input" | "polling" | "result";

/** useAsyncAnalysisPage のオプション型 */
type UseAsyncAnalysisPageOptions<TResult> = {
  /**
   * キャッシュ読み込み関数。
   * - 結果が存在する場合は result を返す
   * - 処理中の場合は status: "pending" | "processing" を返す
   * - キャッシュなしの場合は result: null を返す
   */
  loadCache: () => Promise<{
    result: TResult | null;
    status?: string;
  }>;
  /**
   * タスクステータス取得関数（ポーリング用）。
   */
  checkStatus: () => Promise<{ status: string; error_message?: string }>;
};

/** useAsyncAnalysisPage の戻り値型 */
type UseAsyncAnalysisPageReturn<TResult> = {
  /** 現在のフェーズ */
  phase: AsyncAnalysisPhase;
  /** フェーズを手動で更新する関数 */
  setPhase: React.Dispatch<React.SetStateAction<AsyncAnalysisPhase>>;
  /** 分析結果（result フェーズ時のみ非 null） */
  result: TResult | null;
  /** 結果を更新する関数 */
  setResult: React.Dispatch<React.SetStateAction<TResult | null>>;
  /** エラーメッセージ */
  error: string | null;
  /** エラーを更新する関数 */
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  /** ポーリング開始関数 */
  startPolling: () => void;
  /** ポーリング中フラグ */
  isPolling: boolean;
  /**
   * 分析リクエストを送信した後に呼ぶハンドラ。
   * polling フェーズに遷移してポーリングを開始する。
   */
  transitionToPolling: () => void;
  /**
   * 結果画面から入力画面に戻るハンドラ。
   * result と追加状態をリセットする。
   */
  backToInput: () => void;
};

/**
 * AI 分析ページで共通する phase 管理・ポーリング制御・エラー処理を提供するカスタムフック。
 * GitHubAnalysisPage・CareerAnalysisPage など、
 * 「キャッシュ読み込み → 入力 → ポーリング → 結果」の状態遷移を持つページで利用する。
 */
export function useAsyncAnalysisPage<TResult>({
  loadCache,
  checkStatus,
}: UseAsyncAnalysisPageOptions<TResult>): UseAsyncAnalysisPageReturn<TResult> {
  const [phase, setPhase] = useState<AsyncAnalysisPhase>("loading-cache");
  const [result, setResult] = useState<TResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { startPolling, isPolling } = useTaskPolling({
    checkStatus,
    onCompleted: async () => {
      try {
        const cached = await loadCache();
        if (cached.result) {
          setResult(cached.result);
          setPhase("result");
        } else {
          setPhase("input");
        }
      } catch {
        setPhase("input");
      }
    },
    onFailed: (err) => {
      setError(err);
      setPhase("input");
    },
  });

  /** 初回マウント時にキャッシュを読み込み、フェーズを決定する */
  useEffect(() => {
    let cancelled = false;

    loadCache()
      .then((cached) => {
        if (cancelled) return;
        if (cached.status === "pending" || cached.status === "processing") {
          setPhase("polling");
          return;
        }
        if (cached.result) {
          setResult(cached.result);
          setPhase("result");
        } else {
          setPhase("input");
        }
      })
      .catch(() => {
        if (!cancelled) setPhase("input");
      });

    return () => {
      cancelled = true;
    };
    // 初回マウント時のみ実行するため依存配列は空にする
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** polling フェーズになったらポーリングを開始する */
  useEffect(() => {
    if (phase === "polling" && !isPolling) {
      startPolling();
    }
  }, [phase, isPolling, startPolling]);

  /** polling フェーズへ遷移するハンドラ */
  const transitionToPolling = () => {
    setPhase("polling");
  };

  /** 入力フェーズへ戻るハンドラ */
  const backToInput = () => {
    setPhase("input");
    setResult(null);
  };

  return {
    phase,
    setPhase,
    result,
    setResult,
    error,
    setError,
    startPolling,
    isPolling,
    transitionToPolling,
    backToInput,
  };
}
