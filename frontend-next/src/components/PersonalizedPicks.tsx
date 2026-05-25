"use client";

import type { RecommendResponse } from "@/lib/types";
import { RecommendationCard } from "./RecommendationCard";

interface PersonalizedPicksProps {
  data: RecommendResponse | null;
  loading: boolean;
  error: string | null;
}

export function PersonalizedPicks({ data, loading, error }: PersonalizedPicksProps) {
  if (loading) {
    return (
      <section className="mx-auto max-w-4xl px-4 py-10">
        <h2 className="text-xl font-bold text-gray-900">Personalized Picks</h2>
        <p className="mt-4 text-gray-500">Finding the best spots for you…</p>
        <div className="mt-6 flex justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-zomato border-t-transparent" />
        </div>
      </section>
    );
  }

  if (error && (!data?.items || data.items.length === 0)) {
    return (
      <section className="mx-auto max-w-4xl px-4 py-10">
        <h2 className="text-xl font-bold text-gray-900">Personalized Picks</h2>
        <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      </section>
    );
  }

  if (!data?.items?.length) {
    return null;
  }

  return (
    <section className="mx-auto max-w-4xl px-4 py-10 pb-16">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-xl font-bold text-gray-900">Personalized Picks</h2>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="rounded-full bg-white px-3 py-1 font-medium text-gray-600 shadow-sm">
            {data.used_llm ? "Groq AI" : "Template fallback"}
          </span>
          {data.filter_count != null && (
            <span className="rounded-full bg-white px-3 py-1 font-medium text-gray-600 shadow-sm">
              {data.filter_count} matched
            </span>
          )}
        </div>
      </div>

      {data.summary && (
        <p className="mb-6 text-center text-gray-600">{data.summary}</p>
      )}

      <div className="flex flex-col gap-5">
        {data.items.map((item) => (
          <RecommendationCard key={item.restaurant_id} item={item} />
        ))}
      </div>

      {error && (
        <p className="mt-4 text-center text-sm text-amber-700">{error}</p>
      )}
    </section>
  );
}
