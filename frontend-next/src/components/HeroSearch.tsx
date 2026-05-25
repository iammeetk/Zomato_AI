"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  budgetFromMaxRupees,
  getHealth,
  getLocalities,
  postRecommend,
} from "@/lib/api";
import type { RecommendResponse, SearchFormState } from "@/lib/types";
import { parseCuisines } from "@/lib/utils";
import { QuickTags } from "./QuickTags";

const INITIAL: SearchFormState = {
  chatPrompt: "",
  locality: "",
  cuisine: "",
  budgetMax: 1000,
  cravings: "",
  minRating: 4.0,
  showAdvanced: false,
};

interface HeroSearchProps {
  onResults: (data: RecommendResponse | null) => void;
  onError: (msg: string | null) => void;
  onLoading: (loading: boolean) => void;
}

export function HeroSearch({ onResults, onError, onLoading }: HeroSearchProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const [form, setForm] = useState<SearchFormState>(INITIAL);
  const [metros, setMetros] = useState<string[]>([]);
  const [localities, setLocalities] = useState<string[]>([]);
  const [apiStatus, setApiStatus] = useState<string>("Checking API…");

  useEffect(() => {
    (async () => {
      try {
        const health = await getHealth();
        if (health.dataset === "loaded") {
          let status = `API ready · ${health.row_count ?? "?"} restaurants`;
          if (health.warning) status += ` — ${health.warning}`;
          setApiStatus(status);
          const areas = await getLocalities();
          setMetros(areas.metros.slice(0, 20));
          setLocalities(areas.localities.slice(0, 500));
        } else {
          setApiStatus("API up — run `python -m restaurant_rec ingest`");
        }
      } catch {
        setApiStatus("Backend offline — start: python -m restaurant_rec serve");
      }
    })();
  }, []);

  const update = useCallback(
    <K extends keyof SearchFormState>(key: K, value: SearchFormState[K]) => {
      setForm((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const handleQuickTag = (tag: string) => {
    if (tag === "Near Me") {
      if (metros[0]) update("locality", metros[0]);
      else if (localities[0]) update("locality", localities[0]);
      return;
    }
    if (tag === "Spicy") {
      update("cravings", [form.cravings, "spicy"].filter(Boolean).join(", "));
      return;
    }
    update("cuisine", tag);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onError(null);
    onResults(null);

    const cuisines = parseCuisines(form.cuisine);
    if (!form.locality.trim()) {
      onError("Please enter a locality.");
      return;
    }
    if (cuisines.length === 0) {
      onError("Please enter at least one cuisine.");
      return;
    }

    const notes = [
      form.chatPrompt.trim(),
      form.cravings.trim() ? `Cravings: ${form.cravings.trim()}` : "",
    ]
      .filter(Boolean)
      .join(". ");

    onLoading(true);
    try {
      const data = await postRecommend({
        location: form.locality.trim(),
        budget: budgetFromMaxRupees(form.budgetMax),
        cuisine: cuisines,
        min_rating: form.minRating,
        additional_preferences: notes || null,
      });
      onResults(data);
      if (data.message && (!data.items || data.items.length === 0)) {
        onError(data.message);
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : "Request failed");
    } finally {
      onLoading(false);
    }
  };

  return (
    <section className="relative z-10 mx-auto w-full max-w-3xl px-4 pb-8">
      <div className="rounded-3xl bg-white p-6 shadow-card md:p-8">
        <h1 className="text-center text-xl font-bold text-gray-900 md:text-2xl">
          Find Your Perfect Meal with Zomato AI
        </h1>

        <p className="mt-2 text-center text-xs text-gray-500">{apiStatus}</p>

        <form ref={formRef} onSubmit={handleSubmit} className="mt-6 space-y-5">
          <div className="flex gap-2 rounded-xl border border-gray-200 bg-gray-50 p-2">
            <span className="flex items-center pl-2 text-gray-400" aria-hidden>
              <MicIcon />
            </span>
            <input
              type="text"
              value={form.chatPrompt}
              onChange={(e) => update("chatPrompt", e.target.value)}
              placeholder="Hi! What are you craving today?"
              className="min-w-0 flex-1 bg-transparent py-2 text-sm outline-none placeholder:text-gray-400"
            />
            <button
              type="button"
              onClick={() => formRef.current?.requestSubmit()}
              className="shrink-0 rounded-lg bg-zomato px-5 py-2 text-sm font-semibold text-white transition hover:bg-zomato-dark"
            >
              Send
            </button>
          </div>

          <QuickTags onSelect={handleQuickTag} />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="CITY / LOCALITY">
              <input
                list="locality-options"
                value={form.locality}
                onChange={(e) => update("locality", e.target.value)}
                placeholder="e.g. Bangalore, BTM, Banashankari"
                className={inputClass}
                required
              />
              <datalist id="locality-options">
                {metros.map((m) => (
                  <option key={`metro-${m}`} value={m} />
                ))}
                {localities.map((loc) => (
                  <option key={`loc-${loc}`} value={loc} />
                ))}
              </datalist>
            </Field>

            <Field label="CUISINE">
              <input
                value={form.cuisine}
                onChange={(e) => update("cuisine", e.target.value)}
                placeholder="e.g. North Indian"
                className={inputClass}
                required
              />
            </Field>

            <Field label="BUDGET (MAX ₹ FOR TWO)">
              <input
                type="number"
                min={100}
                max={10000}
                step={50}
                value={form.budgetMax}
                onChange={(e) => update("budgetMax", Number(e.target.value))}
                className={inputClass}
              />
            </Field>

            <Field label="SPECIFIC CRAVINGS">
              <input
                value={form.cravings}
                onChange={(e) => update("cravings", e.target.value)}
                placeholder="e.g. Biryani, Butter Chicken"
                className={inputClass}
              />
            </Field>
          </div>

          <button
            type="button"
            onClick={() => update("showAdvanced", !form.showAdvanced)}
            className="flex items-center gap-1 text-sm font-medium text-gray-700 hover:text-zomato"
          >
            <span
              className={`inline-block transition ${form.showAdvanced ? "rotate-90" : ""}`}
            >
              ▶
            </span>
            More options
          </button>

          {form.showAdvanced && (
            <Field label="MINIMUM RATING (0–5)">
              <input
                type="number"
                min={0}
                max={5}
                step={0.1}
                value={form.minRating}
                onChange={(e) => update("minRating", Number(e.target.value))}
                className={inputClass}
              />
            </Field>
          )}

          <button
            type="submit"
            className="w-full rounded-xl bg-zomato py-3.5 text-base font-bold text-white shadow-md transition hover:bg-zomato-dark disabled:opacity-60"
          >
            Get Recommendations
          </button>
        </form>
      </div>
    </section>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-semibold tracking-wide text-gray-500">
        {label}
      </span>
      {children}
    </label>
  );
}

const inputClass =
  "w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 outline-none transition focus:border-zomato focus:ring-2 focus:ring-zomato/20";

function MicIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z" />
    </svg>
  );
}
