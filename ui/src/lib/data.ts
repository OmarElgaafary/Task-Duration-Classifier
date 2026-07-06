import type { ChartConfig } from "@/components/ui/chart";

export const durationClasses = ["Short", "Standard", "Long-running"] as const;

export const issueTypes = [
  { name: "Bug", count: 23451, percent: 42.42 },
  { name: "Improvement", count: 12990, percent: 23.50 },
  { name: "Sub-task", count: 8588, percent: 15.54 },
  { name: "Task", count: 5065, percent: 9.16 },
  { name: "New Feature", count: 3452, percent: 6.24 },
  { name: "Test", count: 620, percent: 1.12 }
];

export const priorities = [
  { name: "Major", count: 38731, percent: 70.06 },
  { name: "Minor", count: 8912, percent: 16.12 },
  { name: "Critical", count: 2147, percent: 3.88 },
  { name: "Blocker", count: 1979, percent: 3.58 },
  { name: "Trivial", count: 1537, percent: 2.78 },
  { name: "Unknown", count: 722, percent: 1.31 }
];

export const classificationMetrics = [
  {
    className: "Long-running",
    precision: 0.62,
    recall: 0.57,
    f1: 0.59,
    support: 3685
  },
  {
    className: "Short",
    precision: 0.66,
    recall: 0.76,
    f1: 0.70,
    support: 3686
  },
  {
    className: "Standard",
    precision: 0.66,
    recall: 0.62,
    f1: 0.64,
    support: 3686
  }
];

export const aggregateMetrics = [
  {
    label: "Accuracy",
    precision: null,
    recall: null,
    f1: 0.65,
    support: 11057
  },
  {
    label: "Macro avg",
    precision: 0.65,
    recall: 0.65,
    f1: 0.65,
    support: 11057
  },
  {
    label: "Weighted avg",
    precision: 0.65,
    recall: 0.65,
    f1: 0.65,
    support: 11057
  }
];

export const distributionChartConfig = {
  percent: {
    label: "Share",
    color: "hsl(var(--chart-1))"
  }
} satisfies ChartConfig;

export const probabilityChartConfig = {
  probability: {
    label: "Probability",
    color: "hsl(var(--chart-1))"
  }
} satisfies ChartConfig;

export const developerLinks = {
  github: "https://github.com/OmarElgaafary",
  linkedin: "https://www.linkedin.com/in/omar-elgaafary-8b80b6389/",
  huggingFace: "https://huggingface.co/omaradly/jira-task-duration-classifier",
};
