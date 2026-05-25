"use client";

const NAV = [
  { label: "Home", active: true },
  { label: "Dining Out", active: false },
  { label: "Delivery", active: false },
  { label: "Profile", active: false },
];

export function Header() {
  return (
    <header className="relative z-20 flex items-center justify-between px-6 py-4 md:px-10">
      <div className="flex items-baseline gap-0.5">
        <span className="text-2xl font-bold tracking-tight text-zomato md:text-3xl">
          zomato
        </span>
        <span className="text-xl font-semibold text-gray-900 md:text-2xl">AI</span>
      </div>
      <nav className="flex items-center gap-4 text-sm font-medium md:gap-8 md:text-base">
        {NAV.map((item) => (
          <button
            key={item.label}
            type="button"
            className={
              item.active
                ? "text-zomato"
                : "text-gray-800 transition hover:text-zomato"
            }
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
