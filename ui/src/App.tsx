import * as React from "react";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ExternalLink,
  Github,
  Loader2,
  Moon,
  Server,
  Sparkles,
  Sun,
  Terminal
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltipContent
} from "@/components/ui/chart";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import {
  API_BASE_URL,
  getHomeMetadata,
  predictTaskDuration,
  type HomeMetadata,
  type PredictResponse
} from "@/lib/api";
import {
  aggregateMetrics,
  classificationMetrics,
  developerLinks,
  distributionChartConfig,
  durationClasses,
  issueTypes,
  priorities,
  probabilityChartConfig
} from "@/lib/data";
import { cn } from "@/lib/utils";

const issueTypeOptions = [
  "Bug",
  "Improvement",
  "Sub-task",
  "Task",
  "New Feature",
  "Test"
];

const priorityOptions = [
  "Major",
  "Minor",
  "Critical",
  "Blocker",
  "Trivial",
  "Normal"
];

const typewriterWords = ["Short", "Standard", "Long-running"];

function useTypewriter(words: string[]) {
  const [wordIndex, setWordIndex] = React.useState(0);
  const [characterCount, setCharacterCount] = React.useState(0);
  const [deleting, setDeleting] = React.useState(false);

  React.useEffect(() => {
    const currentWord = words[wordIndex];
    const isWordComplete = characterCount === currentWord.length;
    const isWordEmpty = characterCount === 0;
    const delay = isWordComplete && !deleting ? 1250 : deleting ? 45 : 70;

    const timer = window.setTimeout(() => {
      if (!deleting && isWordComplete) {
        setDeleting(true);
        return;
      }

      if (deleting && isWordEmpty) {
        setDeleting(false);
        setWordIndex((current) => (current + 1) % words.length);
        return;
      }

      setCharacterCount((current) => current + (deleting ? -1 : 1));
    }, delay);

    return () => window.clearTimeout(timer);
  }, [characterCount, deleting, wordIndex, words]);

  return words[wordIndex].slice(0, characterCount);
}

function useTheme() {
  const [theme, setTheme] = React.useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    const storedTheme = window.localStorage.getItem("theme");
    if (storedTheme === "dark" || storedTheme === "light") return storedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  React.useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  return {
    theme,
    toggleTheme: () =>
      setTheme((current) => (current === "dark" ? "light" : "dark"))
  };
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatMetric(value: number | null) {
  return value === null ? "-" : value.toFixed(2);
}

function formatProbability(value: number) {
  return `${Math.round(value * 100)}%`;
}

function getLinkHref(url: string) {
  return url.startsWith("TODO") ? "#" : url;
}

function SectionHeading({
  eyebrow,
  title,
  description
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mx-auto max-w-3xl text-center">
      <Badge variant="muted" className="mb-4">
        {eyebrow}
      </Badge>
      <h2 className="text-balance text-3xl font-semibold tracking-normal sm:text-4xl">
        {title}
      </h2>
      <p className="mt-4 text-base leading-7 text-muted-foreground">
        {description}
      </p>
    </div>
  );
}

function DistributionTable({
  rows
}: {
  rows: Array<{ name: string; count: number; percent: number }>;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead className="text-right">Count</TableHead>
          <TableHead className="text-right">Share</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.name}>
            <TableCell className="font-medium">{row.name}</TableCell>
            <TableCell className="text-right tabular-nums">
              {formatNumber(row.count)}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {row.percent.toFixed(2)}%
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function DistributionChart({
  rows
}: {
  rows: Array<{ name: string; percent: number }>;
}) {
  return (
    <ChartContainer config={distributionChartConfig}>
      <BarChart data={rows} margin={{ left: 0, right: 12, top: 8, bottom: 8 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis
          dataKey="name"
          tickLine={false}
          axisLine={false}
          interval={0}
          tick={{ fontSize: 12 }}
        />
        <YAxis tickLine={false} axisLine={false} width={42} />
        <Tooltip
          cursor={{ fill: "hsl(var(--muted))" }}
          content={
            <ChartTooltipContent formatter={(value) => `${value.toFixed(2)}%`} />
          }
        />
        <Bar
          dataKey="percent"
          name="Share"
          radius={[6, 6, 0, 0]}
          fill="var(--color-percent)"
        />
      </BarChart>
    </ChartContainer>
  );
}

function App() {
  const typedWord = useTypewriter(typewriterWords);
  const { theme, toggleTheme } = useTheme();
  const { toast } = useToast();
  const [metadata, setMetadata] = React.useState<HomeMetadata | null>(null);
  const [metadataError, setMetadataError] = React.useState<string | null>(null);
  const [formState, setFormState] = React.useState({
    summary: "",
    description: "",
    issuetype_name: "",
    priority_name: ""
  });
  const [formError, setFormError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [prediction, setPrediction] = React.useState<PredictResponse | null>(null);

  React.useEffect(() => {
    getHomeMetadata()
      .then(setMetadata)
      .catch((error: Error) => setMetadataError(error.message));
  }, []);

  const probabilityData = durationClasses.map((durationClass) => ({
    name: durationClass,
    probability: prediction?.probabilities?.[durationClass] ?? 0
  }));

  const hasProbabilities =
    prediction?.probabilities &&
    durationClasses.some((durationClass) =>
      Boolean(prediction.probabilities?.[durationClass])
    );

  function scrollToPredictor() {
    document
      .getElementById("try-model")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const summary = formState.summary.trim();
    if (!summary) {
      setFormError("Summary is required.");
      return;
    }

    setFormError(null);
    setIsSubmitting(true);
    setPrediction(null);

    const payload = {
      summary,
      ...(formState.description.trim()
        ? { description: formState.description.trim() }
        : {}),
      ...(formState.issuetype_name
        ? { issuetype_name: formState.issuetype_name }
        : {}),
      ...(formState.priority_name
        ? { priority_name: formState.priority_name }
        : {})
    };

    try {
      const response = await predictTaskDuration(payload);
      setPrediction(response);
      toast({
        title: "Prediction complete",
        description: `The model classified this issue as ${response.duration_category}.`
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "The API request failed.";
      setFormError(message);
      toast({
        title: "Prediction failed",
        description: message,
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur">
        <div className="container flex h-16 items-center justify-between gap-4">
          <a href="#top" className="flex items-center gap-2 font-semibold">
            <span className="hidden sm:inline">Task Time Predictor</span>
          </a>
          <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
            <a className="transition-colors hover:text-foreground" href="#docs">
              Docs
            </a>
            <a className="transition-colors hover:text-foreground" href="#metrics">
              Metrics
            </a>
            <a className="transition-colors hover:text-foreground" href="#try-model">
              Try Model
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn(
                "hidden gap-1.5 sm:inline-flex",
                metadataError && "border-destructive/40 text-destructive"
              )}
            >
              <Server className="h-3.5 w-3.5" />
              {metadata ? metadata.status : metadataError ? "API offline" : "Checking"}
            </Badge>
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              title="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </header>

      <main id="top">
        <section className="container grid min-h-[calc(100vh-4rem)] items-center gap-10 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:py-20">
          <div>
            <Badge variant="muted" className="mb-5 gap-2">
              <Sparkles className="h-3.5 w-3.5" />
              FastAPI + Logistic Regression
            </Badge>
            <h1 className="text-balance text-5xl font-semibold tracking-normal sm:text-6xl lg:text-7xl">
              Task Time Predictor
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
              A one-page interface for classifying Jira-style software issues as
              Short, Standard, or Long-running from summary, description, issue
              type, and priority.
            </p>
            <div className="mt-7 flex min-h-8 items-center gap-3 font-mono text-sm text-muted-foreground">
              <span className="rounded-md border bg-card px-2 py-1">predict</span>
              <span className="text-foreground">
                {typedWord}
                <span className="ml-0.5 animate-pulse">|</span>
              </span>
            </div>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button type="button" size="lg" onClick={scrollToPredictor}>
                Try Model
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button type="button" size="lg" variant="outline" asChild>
                <a href={`${API_BASE_URL}/docs`} target="_blank" rel="noreferrer">
                  API Docs
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            </div>
          </div>

          <div className="grid gap-4">
            <Card className="shadow-soft">
              <CardHeader>
                <CardTitle>Model contract</CardTitle>
                <CardDescription>
                  The deployed pipeline turns issue text and metadata into an
                  ordinal duration category.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid grid-cols-3 gap-2 text-center text-sm">
                  {durationClasses.map((durationClass) => (
                    <div
                      key={durationClass}
                      className="rounded-md border bg-muted/40 px-2 py-3 font-medium"
                    >
                      {durationClass}
                    </div>
                  ))}
                </div>
                <Separator />
                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Model</span>
                    <span className="font-medium">
                      {metadata?.model.type ?? "Logistic Regression"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Endpoint</span>
                    <code className="rounded bg-muted px-2 py-1 font-mono">
                      POST /predict
                    </code>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Accuracy</span>
                    <span className="font-medium">0.80</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section id="docs" className="border-t py-20">
          <div className="container">
            <SectionHeading
              eyebrow="Project documentation"
              title="From Jira-style records to a deployed classifier"
              description="The project cleans software issue data, engineers model-ready text, categorical, and numeric features, trains a Logistic Regression classifier, and serves predictions through FastAPI."
            />

            <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
              {[
                ["EDA", "Inspect fields, missing values, text length, and duration distribution."],
                ["Cleaning", "Remove unusable rows and normalize issue records."],
                ["Features", "Build total text, category fields, word counts, and ratios."],
                ["Training", "Fit the Logistic Regression pipeline and save artifacts."],
                ["API", "Load the joblib model and expose prediction endpoints."]
              ].map(([title, description]) => (
                <Card key={title}>
                  <CardHeader>
                    <CardTitle className="text-base">{title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="mt-12 grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
              <div className="space-y-5">
                <h3 className="text-2xl font-semibold">Model design</h3>
                <p className="leading-7 text-muted-foreground">
                  The API recreates the core features expected by the trained
                  pipeline: combined text, issue type, priority, project
                  metadata, created date parts, character counts, word counts,
                  description presence, labels, assignee status, votes, and
                  watches.
                </p>
                <p className="leading-7 text-muted-foreground">
                  Logistic Regression is used as a lightweight baseline for
                  sparse text classification. The target is ordinal, so the
                  categories should be read as Short -&gt; Standard -&gt;
                  Long-running rather than unrelated labels.
                </p>
              </div>

              <Tabs defaultValue="issue-types">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="issue-types">Issue types</TabsTrigger>
                  <TabsTrigger value="priorities">Priorities</TabsTrigger>
                </TabsList>
                <TabsContent value="issue-types">
                  <div className="grid gap-6 lg:grid-cols-2">
                    <DistributionChart rows={issueTypes} />
                    <DistributionTable rows={issueTypes} />
                  </div>
                </TabsContent>
                <TabsContent value="priorities">
                  <div className="grid gap-6 lg:grid-cols-2">
                    <DistributionChart rows={priorities} />
                    <DistributionTable rows={priorities} />
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </section>

        <section id="metrics" className="border-t bg-muted/25 py-20">
          <div className="container">
            <SectionHeading
              eyebrow="Model evaluation"
              title="Actual metrics from the saved classification report"
              description="The current test report shows 0.80 accuracy across 20,315 evaluated issues. The confusion matrix is useful because neighboring mistakes can still be operationally helpful."
            />

            <div className="mt-12 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Classification report</CardTitle>
                  <CardDescription>
                    Values are copied from model_tests/classification_report.txt.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Class</TableHead>
                        <TableHead className="text-right">Precision</TableHead>
                        <TableHead className="text-right">Recall</TableHead>
                        <TableHead className="text-right">F1</TableHead>
                        <TableHead className="text-right">Support</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {classificationMetrics.map((row) => (
                        <TableRow key={row.className}>
                          <TableCell className="font-medium">{row.className}</TableCell>
                          <TableCell className="text-right tabular-nums">
                            {row.precision.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {row.recall.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {row.f1.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatNumber(row.support)}
                          </TableCell>
                        </TableRow>
                      ))}
                      {aggregateMetrics.map((row) => (
                        <TableRow key={row.label}>
                          <TableCell className="font-medium">{row.label}</TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatMetric(row.precision)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatMetric(row.recall)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatMetric(row.f1)}
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatNumber(row.support)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <Alert variant="muted">
                    <AlertDescription>
                      Since Short, Standard, and Long-running are ordered, a
                      one-step miss can still be useful for planning. For example,
                      confusing Short with Standard is less severe than jumping
                      from Short to Long-running.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Confusion matrix</CardTitle>
                  <CardDescription>
                    Saved evaluation artifact from model_tests.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex justify-center">
                  <img
                    src="/assets/confusion_matrix.png"
                    alt="Confusion matrix for Short, Standard, and Long-running duration classes"
                    className="mx-auto block w-full max-w-[760px] rounded-md border bg-background object-contain"
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section id="try-model" className="border-t py-20">
          <div className="container">
            <SectionHeading
              eyebrow="Try model"
              title="Classify a software issue"
              description="Send a task summary, optional description, and optional Jira-style metadata to the FastAPI model endpoint."
            />

            <div className="mt-12 grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Prediction input</CardTitle>
                  <CardDescription>
                    Required fields are validated before the API call.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form className="space-y-5" onSubmit={handleSubmit}>
                    <div className="space-y-2">
                      <Label htmlFor="summary">Summary</Label>
                      <Input
                        id="summary"
                        required
                        value={formState.summary}
                        placeholder="Fix CORS error on /api/v2/users endpoint"
                        onChange={(event) =>
                          setFormState((current) => ({
                            ...current,
                            summary: event.target.value
                          }))
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Textarea
                        id="description"
                        value={formState.description}
                        placeholder="Frontend requests are failing in production because the response is missing an Access-Control-Allow-Origin header."
                        onChange={(event) =>
                          setFormState((current) => ({
                            ...current,
                            description: event.target.value
                          }))
                        }
                      />
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="issuetype_name">Issue type</Label>
                        <Select
                          id="issuetype_name"
                          value={formState.issuetype_name}
                          onChange={(event) =>
                            setFormState((current) => ({
                              ...current,
                              issuetype_name: event.target.value
                            }))
                          }
                        >
                          <option value="">Optional</option>
                          {issueTypeOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="priority_name">Priority</Label>
                        <Select
                          id="priority_name"
                          value={formState.priority_name}
                          onChange={(event) =>
                            setFormState((current) => ({
                              ...current,
                              priority_name: event.target.value
                            }))
                          }
                        >
                          <option value="">Optional</option>
                          {priorityOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </Select>
                      </div>
                    </div>

                    {formError ? (
                      <Alert variant="destructive">
                        <AlertDescription>{formError}</AlertDescription>
                      </Alert>
                    ) : null}

                    <Button type="submit" className="w-full" disabled={isSubmitting}>
                      {isSubmitting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Terminal className="h-4 w-4" />
                      )}
                      Predict duration
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Prediction result</CardTitle>
                  <CardDescription>
                    Probabilities appear when the API returns predict_proba data.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {isSubmitting ? (
                    <div className="space-y-4">
                      <Skeleton className="h-16 w-full" />
                      <Skeleton className="h-[280px] w-full" />
                    </div>
                  ) : prediction ? (
                    <>
                      <div className="flex flex-col gap-4 rounded-lg border bg-muted/30 p-5 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <div className="text-sm text-muted-foreground">
                            Duration category
                          </div>
                          <div className="mt-1 text-3xl font-semibold">
                            {prediction.duration_category}
                          </div>
                        </div>
                        <Badge variant="secondary" className="w-fit gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Classified
                        </Badge>
                      </div>

                      {hasProbabilities ? (
                        <ChartContainer config={probabilityChartConfig}>
                          <BarChart
                            data={probabilityData}
                            margin={{ left: 0, right: 12, top: 8, bottom: 8 }}
                          >
                            <CartesianGrid vertical={false} strokeDasharray="3 3" />
                            <XAxis
                              dataKey="name"
                              tickLine={false}
                              axisLine={false}
                              interval={0}
                              tick={{ fontSize: 12 }}
                            />
                            <YAxis
                              tickFormatter={(value) => `${value * 100}%`}
                              domain={[0, 1]}
                              tickLine={false}
                              axisLine={false}
                              width={42}
                            />
                            <Tooltip
                              cursor={{ fill: "hsl(var(--muted))" }}
                              content={
                                <ChartTooltipContent
                                  formatter={(value) => formatProbability(value)}
                                />
                              }
                            />
                            <Bar
                              dataKey="probability"
                              name="Probability"
                              radius={[6, 6, 0, 0]}
                              fill="var(--color-probability)"
                            />
                          </BarChart>
                        </ChartContainer>
                      ) : (
                        <Alert variant="muted">
                          <AlertDescription>
                            This API response did not include probabilities, so the
                            chart is unavailable for this prediction.
                          </AlertDescription>
                        </Alert>
                      )}
                    </>
                  ) : (
                    <div className="flex min-h-[360px] flex-col items-center justify-center rounded-lg border border-dashed bg-muted/20 p-8 text-center">
                      <BarChart3 className="mb-4 h-10 w-10 text-muted-foreground" />
                      <p className="max-w-sm text-sm leading-6 text-muted-foreground">
                        Results will appear here after the model responds from
                        POST /predict.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-10">
        <div className="container flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="max-w-2xl">
            <div className="font-semibold">Omar Adly</div>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Engineering-minded developer interested in mathematics, data
              visualization, machine learning, backend APIs, and practical tools.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              ["GitHub", developerLinks.github, Github],
              ["LinkedIn", developerLinks.linkedin, ExternalLink],
              ["Hugging Face", developerLinks.huggingFace, ExternalLink],
            ].map(([label, url, Icon]) => (
              <Button key={String(label)} variant="outline" size="sm" asChild>
                <a
                  href={getLinkHref(String(url))}
                  target={String(url).startsWith("TODO") ? undefined : "_blank"}
                  rel="noreferrer"
                  aria-label={`${label} profile`}
                  title={String(url).startsWith("TODO") ? String(url) : String(label)}
                >
                  <Icon className="h-4 w-4" />
                  {String(label)}
                </a>
              </Button>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
