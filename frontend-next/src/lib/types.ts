export type UserBudget = "low" | "medium" | "high";

export interface RecommendRequest {
  location: string;
  budget: UserBudget;
  cuisine: string[];
  min_rating: number;
  additional_preferences?: string | null;
}

export interface RecommendationItem {
  restaurant_id: string;
  name: string;
  cuisine: string;
  rating: number | null;
  estimated_cost: string;
  explanation: string;
  rank: number;
}

export interface RecommendResponse {
  items: RecommendationItem[];
  summary: string | null;
  used_llm: boolean;
  warnings: string[];
  filter_count: number;
  returned_count: number;
  dataset_snapshot_id?: string | null;
  message?: string | null;
}

export interface HealthResponse {
  status: string;
  dataset: string;
  row_count?: number | null;
  schema_version?: string | null;
  warning?: string | null;
}

export interface SearchFormState {
  chatPrompt: string;
  locality: string;
  cuisine: string;
  budgetMax: number;
  cravings: string;
  minRating: number;
  showAdvanced: boolean;
}
