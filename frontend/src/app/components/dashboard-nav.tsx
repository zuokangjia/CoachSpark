"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkle, LayoutDashboard, Award, Menu, X, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/lib/store/theme-store";

const navItems = [
  { href: "/", label: "投递看板", icon: LayoutDashboard, matchPattern: (path: string) => path === "/" },
  { href: "/offers", label: "Offer 比较", icon: Award, matchPattern: (path: string) => path.startsWith("/offers") },
];

export function DashboardNav() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { resolved, toggle } = useThemeStore();

  return (
    <nav className="sticky top-0 z-50 border-b border-border/60 bg-surface/80 backdrop-blur-md shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link
          href="/"
          className="group flex items-center gap-2.5"
          onClick={() => setMobileOpen(false)}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand to-brand-hover shadow-sm transition-transform group-hover:scale-105">
            <Sparkle className="h-4 w-4 text-text-inverse" />
          </div>
          <span className="text-lg font-bold tracking-tight text-text-primary">
            Coach<span className="text-brand">Spark</span>
          </span>
        </Link>

        <div className="hidden items-center gap-1 sm:flex">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.matchPattern(pathname);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-brand-subtle text-brand-text"
                    : "text-text-secondary hover:bg-surface-secondary hover:text-text-primary",
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
                {isActive && (
                  <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-brand" />
                )}
              </Link>
            );
          })}

          <div className="ml-1 h-5 w-px bg-border" />

          <button
            onClick={toggle}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-text-secondary hover:bg-surface-secondary hover:text-text-primary transition-colors"
            aria-label={resolved === "dark" ? "切换为浅色模式" : "切换为深色模式"}
          >
            {resolved === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>
        </div>

        <button
          className="flex h-9 w-9 items-center justify-center rounded-lg text-text-secondary hover:bg-surface-secondary hover:text-text-primary sm:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? "关闭菜单" : "打开菜单"}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="border-t border-border/60 bg-surface px-4 py-3 sm:hidden">
          <div className="flex flex-col gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.matchPattern(pathname);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-brand-subtle text-brand-text"
                      : "text-text-secondary hover:bg-surface-secondary hover:text-text-primary",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}

            <div className="my-1 h-px bg-border" />

            <button
              onClick={() => {
                toggle();
                setMobileOpen(false);
              }}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium text-text-secondary hover:bg-surface-secondary hover:text-text-primary transition-colors"
            >
              {resolved === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
              {resolved === "dark" ? "浅色模式" : "深色模式"}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
