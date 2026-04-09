import { useState, useEffect, useCallback, useRef } from "react";

import { ApiError, type AppErrorState, toAppError } from "../utils/appError";

interface TaskStatus {
  status: string;
  error_message?: string;
  error_code?: string;
  error_id?: string;
  retry_after?: number;
}

interface UseTaskPollingOptions {
  /** ステータス取得関数 */
  checkStatus: () => Promise<TaskStatus>;
  /** 完了時コールバック */
  onCompleted: () => void;
  /** 失敗時コールバック */
  onFailed: (error: AppErrorState) => void;
  /** ポーリング間隔（ms、デフォルト: 5000） */
  intervalMs?: number;
}

/**
 * バックグラウンドタスクのステータスをポーリングする汎用フック。
 * unmount 時に clearInterval するが、バックエンド処理はそのまま継続される。
 */
export function useTaskPolling(options: UseTaskPollingOptions) {
  const { checkStatus, onCompleted, onFailed, intervalMs = 5000 } = options;
  const [isPolling, setIsPolling] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);
  const callbacksRef = useRef({ onCompleted, onFailed, checkStatus });

  // コールバックを ref で最新に保つ（レンダー外で更新）
  useEffect(() => {
    callbacksRef.current = { onCompleted, onFailed, checkStatus };
  });

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const startPolling = useCallback(() => {
    setIsPolling(true);
    setStatus("pending");
  }, []);

  useEffect(() => {
    if (!isPolling) return;

    const poll = async () => {
      try {
        const data = await callbacksRef.current.checkStatus();
        setStatus(data.status);

        if (data.status === "completed") {
          stopPolling();
          callbacksRef.current.onCompleted();
        } else if (data.status === "failed") {
          stopPolling();
          callbacksRef.current.onFailed(
            toAppError(
              new ApiError({
                code: data.error_code ?? "INTERNAL_ERROR",
                message: data.error_message || "処理に失敗しました",
                retryAfter:
                  typeof data.retry_after === "number"
                    ? data.retry_after
                    : null,
                errorId: data.error_id,
              }),
            ),
          );
        }
      } catch {
        // ネットワークエラーは無視してリトライ
      }
    };

    // 初回即実行
    poll();
    intervalRef.current = window.setInterval(poll, intervalMs);

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isPolling, intervalMs, stopPolling]);

  return { startPolling, stopPolling, isPolling, status };
}
