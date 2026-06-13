"use client";

import type { ComponentType } from "react";
import { hapticSelection } from "@/lib/telegram";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;

export type TabKey = "home" | "activity" | "settings" | "admin";

export interface TabDef {
  key: TabKey;
  label: string;
  icon: IconType;
}

interface TabBarProps {
  tabs: TabDef[];
  active: TabKey;
  onChange: (key: TabKey) => void;
}

/** Fixed, safe-area-aware bottom navigation. */
export function TabBar({ tabs, active, onChange }: TabBarProps) {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-30 border-t border-black/[0.05] dark:border-white/[0.07] bg-tg-bg/95 backdrop-blur-xl pb-safe"
      aria-label="Primary"
    >
      <div className="mx-auto flex w-full max-w-md items-stretch">
        {tabs.map((tab) => {
          const isActive = tab.key === active;
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => {
                if (!isActive) hapticSelection();
                onChange(tab.key);
              }}
              aria-current={isActive ? "page" : undefined}
              className="group relative flex flex-1 flex-col items-center justify-center gap-1 py-2.5 transition"
            >
              {isActive && (
                <span
                  aria-hidden
                  className="absolute top-0 h-0.5 w-8 rounded-full bg-brand"
                />
              )}
              <span
                className={`flex h-7 w-12 items-center justify-center rounded-full transition ${
                  isActive ? "bg-brand/12 text-brand" : "text-tg-hint"
                }`}
              >
                <Icon
                  className={`h-[22px] w-[22px] transition ${
                    isActive ? "scale-105" : "group-active:scale-95"
                  }`}
                  aria-hidden
                />
              </span>
              <span
                className={`text-[10px] font-semibold leading-none transition ${
                  isActive ? "text-brand" : "text-tg-hint"
                }`}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
