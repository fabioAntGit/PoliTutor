import type { ComponentProps } from "react";
import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/theme/theme-provider";
import { cn } from "@/lib/utils";

type ThemeToggleProps = Omit<ComponentProps<typeof Button>, "onClick" | "children">;

export function ThemeToggle({ className, variant = "ghost", size = "icon", ...props }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <Button
      type="button"
      variant={variant}
      size={size}
      onClick={toggleTheme}
      aria-label={isDark ? "Ativar modo claro" : "Ativar modo escuro"}
      title={isDark ? "Modo claro" : "Modo escuro"}
      className={cn("relative", className)}
      {...props}
    >
      <Sun
        className={cn(
          "size-[18px] transition-all duration-300",
          isDark ? "scale-0 -rotate-90 opacity-0" : "scale-100 rotate-0 opacity-100",
        )}
      />
      <Moon
        className={cn(
          "absolute size-[18px] transition-all duration-300",
          isDark ? "scale-100 rotate-0 opacity-100" : "scale-0 rotate-90 opacity-0",
        )}
      />
    </Button>
  );
}
