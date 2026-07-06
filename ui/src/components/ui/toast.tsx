import * as React from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Toast = {
  id: number;
  title: string;
  description?: string;
  variant?: "default" | "destructive";
};

type ToastContextValue = {
  toast: (toast: Omit<Toast, "id">) => void;
};

const ToastContext = React.createContext<ToastContextValue | null>(null);

function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const toast = React.useCallback((toastInput: Omit<Toast, "id">) => {
    const id = Date.now();
    setToasts((current) => [...current, { id, ...toastInput }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== id));
    }, 4500);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-50 flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2"
      >
        {toasts.map((item) => (
          <div
            key={item.id}
            className={cn(
              "rounded-lg border bg-background p-4 text-sm shadow-soft",
              item.variant === "destructive" && "border-destructive/40"
            )}
          >
            <div className="flex items-start gap-3">
              <div className="min-w-0 flex-1">
                <div className="font-medium">{item.title}</div>
                {item.description ? (
                  <div className="mt-1 text-muted-foreground">
                    {item.description}
                  </div>
                ) : null}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                aria-label="Dismiss notification"
                onClick={() =>
                  setToasts((current) =>
                    current.filter((toastItem) => toastItem.id !== item.id)
                  )
                }
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside ToastProvider.");
  }
  return context;
}

export { ToastProvider, useToast };
