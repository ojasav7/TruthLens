export type CaseStatus = "open" | "in_review" | "closed";
export type CasePriority = "high" | "medium" | "low";

export interface CaseItem {
  id: string;
  title: string;
  status: CaseStatus;
  priority: CasePriority;
  summary: string;
  created: string;
  updated: string;
  analyst: string;
  modalities: string[];
  evidenceCount: number;
  threatScore: number;
}

export const STATUS_COLORS: Record<CaseStatus, string> = {
  open: "bg-primary",
  in_review: "bg-amber",
  closed: "bg-muted-foreground",
};

export const STATUS_LABELS: Record<CaseStatus, string> = {
  open: "Open",
  in_review: "In Review",
  closed: "Closed",
};

export const PRIORITY_COLORS: Record<CasePriority, string> = {
  high: "border-l-destructive",
  medium: "border-l-amber",
  low: "border-l-primary",
};

export const MOCK_CASES: CaseItem[] = [
  {
    id: "CASE-2026-0847",
    title: "Viral Deepfake of CEO",
    status: "open",
    priority: "high",
    summary: "Deepfake video of company CEO circulating on social media, making false claims about bankruptcy. Requires immediate analysis.",
    created: "2026-08-28 14:23",
    updated: "2026-08-30 09:15",
    analyst: "OT",
    modalities: ["video", "audio"],
    evidenceCount: 24,
    threatScore: 87,
  },
  {
    id: "CASE-2026-0846",
    title: "Fake News Article Network",
    status: "in_review",
    priority: "high",
    summary: "Coordinated network of fake news articles spreading misinformation about election results. 12 articles identified across 5 domains.",
    created: "2026-08-27 10:45",
    updated: "2026-08-29 16:30",
    analyst: "JD",
    modalities: ["text"],
    evidenceCount: 18,
    threatScore: 72,
  },
  {
    id: "CASE-2026-0845",
    title: "Suspicious Product Image",
    status: "open",
    priority: "medium",
    summary: "Product images on e-commerce site show signs of AI generation. Customers reporting items don't match photos.",
    created: "2026-08-26 08:12",
    updated: "2026-08-28 11:45",
    analyst: "MK",
    modalities: ["image"],
    evidenceCount: 8,
    threatScore: 54,
  },
  {
    id: "CASE-2026-0844",
    title: "Voice Clone Phishing Campaign",
    status: "in_review",
    priority: "high",
    summary: "Multiple reports of AI-generated voice calls impersonating executives. 3 successful wire transfers detected.",
    created: "2026-08-25 16:30",
    updated: "2026-08-27 09:20",
    analyst: "OT",
    modalities: ["audio"],
    evidenceCount: 31,
    threatScore: 91,
  },
  {
    id: "CASE-2026-0843",
    title: "Manipulated Press Photo",
    status: "closed",
    priority: "low",
    summary: "Press photo from rally showed signs of crowd manipulation. Analysis confirmed minor digital editing.",
    created: "2026-08-20 11:00",
    updated: "2026-08-22 14:15",
    analyst: "JD",
    modalities: ["image"],
    evidenceCount: 5,
    threatScore: 23,
  },
  {
    id: "CASE-2026-0842",
    title: "AI-Generated Academic Paper",
    status: "closed",
    priority: "medium",
    summary: "Submitted paper flagged for AI generation. NLP analysis confirmed 94% probability of LLM authorship.",
    created: "2026-08-18 09:30",
    updated: "2026-08-20 10:45",
    analyst: "MK",
    modalities: ["text"],
    evidenceCount: 12,
    threatScore: 68,
  },
];

export const MODALITY_ICONS: Record<string, string> = {
  text: "T",
  image: "\u{1F5BC}",
  video: "\u{1F3AC}",
  audio: "\u{1F50A}",
};
