import type { SetupFormValues } from "@/lib/schemas/setup";

export type IAEduConfig = Omit<SetupFormValues, "projectId">;