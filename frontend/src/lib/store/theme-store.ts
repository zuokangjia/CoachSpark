import { create } from "zustand";

export type ThemeMode = "light" | "dark" | "system";

interface ThemeState {
  mode: ThemeMode;
  resolved: "light" | "dark";
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
}

function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function getStoredMode(): ThemeMode {
  try {
    const stored = localStorage.getItem("theme-mode");
    if (stored === "light" || stored === "dark" || stored === "system") return stored;
  } catch {}
  return "system";
}

function applyTheme(mode: ThemeMode) {
  const resolved = mode === "system" ? getSystemTheme() : mode;
  document.documentElement.setAttribute("data-theme", resolved);
  return resolved;
}

export const useThemeStore = create<ThemeState>((set, get) => {
  const mode = typeof window !== "undefined" ? getStoredMode() : "system";

  if (typeof window !== "undefined") {
    applyTheme(mode);

    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (get().mode === "system") {
        set({ resolved: getSystemTheme() });
        applyTheme("system");
      }
    });
  }

  return {
    mode,
    resolved: mode === "system" ? getSystemTheme() : mode,
    setMode: (newMode: ThemeMode) => {
      try {
        localStorage.setItem("theme-mode", newMode);
      } catch {}
      const resolved = applyTheme(newMode);
      set({ mode: newMode, resolved });
    },
    toggle: () => {
      const current = get().resolved;
      const newMode = current === "dark" ? "light" : "dark";
      try {
        localStorage.setItem("theme-mode", newMode);
      } catch {}
      applyTheme(newMode);
      set({ mode: newMode, resolved: newMode });
    },
  };
});
