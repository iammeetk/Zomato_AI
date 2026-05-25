"use client";

import Image from "next/image";
import type { RecommendationItem } from "@/lib/types";
import { foodImageUrl } from "@/lib/utils";

interface RecommendationCardProps {
  item: RecommendationItem;
}

export function RecommendationCard({ item }: RecommendationCardProps) {
  const rating =
    item.rating != null && !Number.isNaN(item.rating)
      ? item.rating.toFixed(1)
      : "N/A";

  return (
    <article className="flex overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition hover:shadow-md">
      <div className="relative h-36 w-36 shrink-0 sm:h-40 sm:w-44">
        <Image
          src={foodImageUrl(item.cuisine, item.restaurant_id)}
          alt={item.name}
          fill
          className="object-cover"
          sizes="(max-width: 640px) 144px, 176px"
          unoptimized
        />
      </div>
      <div className="flex min-w-0 flex-1 flex-col justify-center gap-2 p-4 sm:p-5">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-lg font-bold text-gray-900">{item.name}</h3>
          <span className="shrink-0 text-sm font-semibold text-amber-500">
            {rating} ★
          </span>
        </div>
        <p className="text-sm text-gray-500">{item.cuisine}</p>
        <p className="text-sm font-medium text-gray-700">{item.estimated_cost}</p>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            AI Reason:
          </p>
          <p className="mt-1 text-sm leading-relaxed text-gray-700">
            {item.explanation}
          </p>
        </div>
      </div>
    </article>
  );
}
