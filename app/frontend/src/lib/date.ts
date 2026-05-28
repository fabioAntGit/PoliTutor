import { formatDistanceToNow } from "date-fns";
import { pt } from "date-fns/locale";

function parseAsUtc(iso: string): Date {
  const hasTimezone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasTimezone ? iso : `${iso}Z`);
}

export function formatRelativeDate(iso: string): string {
  return formatDistanceToNow(parseAsUtc(iso), { addSuffix: true, locale: pt });
}
