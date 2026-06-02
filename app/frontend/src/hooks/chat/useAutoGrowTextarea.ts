import { useEffect, useRef } from "react";

export function useAutoGrowTextarea(dependency: string, maxHeight: number = 160) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, [dependency, maxHeight]);

  return textareaRef;
}