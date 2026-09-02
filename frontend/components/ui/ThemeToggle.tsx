"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

const OPTIONS = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
] as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <div className="h-9 w-[132px] rounded-lg skeleton" aria-hidden />;
  }

  return (
    <div className="flex items-center gap-0.5 rounded-lg border border-default bg-subtle p-0.5" role="radiogroup" aria-label="Theme">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          role="radio"
          aria-checked={theme === opt.value}
          onClick={() => setTheme(opt.value)}
          className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
            theme === opt.value
              ? "bg-brand-600 text-white"
              : "text-muted hover:text-current"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
