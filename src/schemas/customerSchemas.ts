import { z } from "zod";

// Schema for customer creation
export const customerCreateSchema = z.object({
  name: z.string().min(1, "会社名は必須です"),
  contact_email: z
    .string()
    .min(1, "メールアドレスは必須です")
    .email("有効なメールアドレスを入力してください"),
  address: z.string().optional(),
});

export type CustomerCreateFormValues = z.infer<typeof customerCreateSchema>;
