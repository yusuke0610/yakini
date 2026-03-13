export function parseUsernameFromToken(token: string | null): string | null {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return (payload.sub as string) ?? null;
  } catch {
    return null;
  }
}
