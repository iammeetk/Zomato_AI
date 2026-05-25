/** Stable placeholder image from cuisine name */
export function foodImageUrl(cuisine: string, seed: string): string {
  const query = encodeURIComponent(cuisine.split(",")[0]?.trim() || "indian food");
  return `https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop&q=80&sig=${encodeURIComponent(seed)}`;
}

export function parseCuisines(raw: string): string[] {
  return raw
    .split(/[,|]/)
    .map((c) => c.trim())
    .filter(Boolean);
}
