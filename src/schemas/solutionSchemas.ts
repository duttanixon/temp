import { z } from "zod";

// Schema for solution update
export const solutionUpdateSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  version: z.string().optional(),
  compatibility: z.array(z.string()).optional(),
  status: z.enum(["ACTIVE", "BETA", "DEPRECATED"]).optional(),
});

export type SolutionUpdateFormValues = z.infer<typeof solutionUpdateSchema>;

// Schema for solution creation
export const solutionCreateSchema = z.object({
  name: z.string().min(1, "名前は必須です"),
  description: z.string().optional(),
  version: z.string().min(1, "バージョンは必須です"),
  compatibility: z
    .array(z.string())
    .min(1, "少なくとも1つのデバイスタイプを選択してください"),
  status: z.enum(["ACTIVE", "BETA", "DEPRECATED"]).default("ACTIVE"),
});

export type SolutionCreateFormValues = z.infer<typeof solutionCreateSchema>;
export type SolutionCreateFormInput = z.input<typeof solutionCreateSchema>;
