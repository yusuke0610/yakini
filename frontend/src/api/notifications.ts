import { request } from "./client";
import { PATHS } from "./paths";

export interface Notification {
  id: string;
  task_type: string;
  status: "completed" | "failed";
  title: string;
  message: string | null;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCountResponse {
  count: number;
}

/**
 * 最新30件の通知を取得します。
 */
export function getNotifications(): Promise<Notification[]> {
  return request<Notification[]>(PATHS.notifications.base);
}

/**
 * 未読件数を取得します。
 */
export function getUnreadCount(): Promise<UnreadCountResponse> {
  return request<UnreadCountResponse>(PATHS.notifications.unreadCount);
}

/**
 * 指定された通知を既読にします。
 */
export function markAsRead(notificationId: string): Promise<Notification> {
  return request<Notification>(PATHS.notifications.read(notificationId), {
    method: "PATCH",
  });
}

/**
 * 全通知を既読にします。
 */
export function markAllAsRead(): Promise<{ updated: number }> {
  return request<{ updated: number }>(PATHS.notifications.readAll, {
    method: "POST",
  });
}
