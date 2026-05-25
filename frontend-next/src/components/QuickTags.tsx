"use client";

const TAGS = ["Italian", "Spicy", "Dessert", "Near Me"];

interface QuickTagsProps {
  onSelect: (tag: string) => void;
}

export function QuickTags({ onSelect }: QuickTagsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {TAGS.map((tag) => (
        <button
          key={tag}
          type="button"
          onClick={() => onSelect(tag)}
          className="rounded-full border border-gray-300 bg-white px-4 py-1.5 text-sm font-medium text-gray-800 transition hover:border-zomato hover:text-zomato"
        >
          {tag}
        </button>
      ))}
    </div>
  );
}
