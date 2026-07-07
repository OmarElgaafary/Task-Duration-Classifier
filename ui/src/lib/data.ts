import type { ChartConfig } from "@/components/ui/chart";

export const durationClasses = ["Short", "Standard", "Long-running"] as const;

export const issueTypes = [
  { name: "Bug", count: 43753, percent: 43.08 },
  { name: "Improvement", count: 23849, percent: 23.48 },
  { name: "Sub-task", count: 15924, percent: 15.68 },
  { name: "Task", count: 8600, percent: 8.47 },
  { name: "New Feature", count: 5888, percent: 5.80 },
  { name: "Test", count: 1265, percent: 1.25 }
];

export const priorities = [
  { name: "Major", count: 70579, percent: 69.49 },
  { name: "Minor", count: 16821, percent: 16.56 },
  { name: "Critical", count: 4049, percent: 3.99 },
  { name: "Blocker", count: 3825, percent: 3.77 },
  { name: "Trivial", count: 2810, percent: 2.77 },
  { name: "Normal", count: 994, percent: 0.98 }
];

export const classificationMetrics = [
  {
    className: "Long-running",
    precision: 0.79,
    recall: 0.71,
    f1: 0.74,
    support: 6771
  },
  {
    className: "Short",
    precision: 0.85,
    recall: 0.87,
    f1: 0.86,
    support: 6772
  },
  {
    className: "Standard",
    precision: 0.76,
    recall: 0.81,
    f1: 0.79,
    support: 6772
  }
];

export const aggregateMetrics = [
  {
    label: "Accuracy",
    precision: null,
    recall: null,
    f1: 0.80,
    support: 20315
  },
  {
    label: "Macro avg",
    precision: 0.80,
    recall: 0.80,
    f1: 0.80,
    support: 20315
  },
  {
    label: "Weighted avg",
    precision: 0.80,
    recall: 0.80,
    f1: 0.80,
    support: 20315
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
