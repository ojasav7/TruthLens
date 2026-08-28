import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getVerdictColor(verdict: string) {
  switch (verdict) {
    case "Low": return "emerald";
    case "Review Needed": return "amber";
    case "High Risk": return "crimson";
    default: return "amber";
  }
}

export function getVerdictIcon(verdict: string) {
  switch (verdict) {
    case "Low": return "🟢";
    case "Review Needed": return "🟡";
    case "High Risk": return "🔴";
    default: return "⚪";
  }
}

export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
