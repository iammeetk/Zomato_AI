"use client";

import { useState } from "react";
import { Header } from "@/components/Header";
import { HeroSearch } from "@/components/HeroSearch";
import { PersonalizedPicks } from "@/components/PersonalizedPicks";
import type { RecommendResponse } from "@/lib/types";

export default function HomePage() {
  const [results, setResults] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="min-h-screen">
      <div className="hero-bg pb-4 pt-2">
        <Header />
        <HeroSearch
          onResults={setResults}
          onError={setError}
          onLoading={setLoading}
        />
      </div>

      <PersonalizedPicks data={results} loading={loading} error={error} />
    </div>
  );
}
