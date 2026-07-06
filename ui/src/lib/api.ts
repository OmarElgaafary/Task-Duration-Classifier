export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export type DurationClass = "Short" | "Standard" | "Long-running";

export type HomeMetadata = {
  name: string;
  description: string;
  status: string;
  model: {
    type: string;
    classes: DurationClass[];
  };
  endpoints: Record<string, string>;
};

export type PredictRequest = {
  summary: string;
  description?: string;
  issuetype_name?: string;
  priority_name?: string;
};

export type PredictResponse = {
  duration_category: DurationClass | string;
  probabilities?: Partial<Record<DurationClass, number>>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getHomeMetadata() {
  return request<HomeMetadata>("/");
}

export function predictTaskDuration(payload: PredictRequest) {
  return request<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
