import type {
  HealthResponse,
  RecommendRequest,
  RecommendResponse,
  UserBudget,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

/** Map max ₹ for two (UI) to backend budget band (Phase 1 thresholds). */
export function budgetFromMaxRupees(max: number): UserBudget {
  if (max <= 400) return "low";
  if (max <= 1000) return "medium";
  return "high";
}

export function formatApiError(detail: unknown): string {
  if (!detail) return "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const row = item as { loc?: string[]; msg?: string };
        const loc = row.loc?.filter((p) => p !== "body").join(".") ?? "";
        return loc ? `${loc}: ${row.msg}` : row.msg;
      })
      .join("; ");
  }
  return JSON.stringify(detail);
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  const text = await response.text();
  let data: { detail?: unknown; message?: string } | null = null;
  if (text) {
    try {
      data = JSON.parse(text) as { detail?: unknown; message?: string };
    } catch {
      data = { detail: text };
    }
  }
  if (!response.ok) {
    throw new Error(
      formatApiError(data?.detail ?? data?.message) || `HTTP ${response.status}`,
    );
  }
  return data as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>("/health");
}

export interface LocalitiesResponse {
  metros: string[];
  localities: string[];
}

export async function getLocalities(): Promise<LocalitiesResponse> {
  return fetchJson<LocalitiesResponse>("/v1/localities");
}

export async function postRecommend(
  body: RecommendRequest,
): Promise<RecommendResponse> {
  return fetchJson<RecommendResponse>("/v1/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export { API_BASE };
