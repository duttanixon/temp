import { z } from "zod";

export const userCreateSchema = z
  .object({
    first_name: z.string().min(1, "名は必須です"),
    last_name: z.string().min(1, "姓は必須です"),
    email: z
      .string()
      .min(1, "メールアドレスは必須です")
      .email("有効なメールアドレスを入力してください"),
    role: z.enum(["ADMIN", "ENGINEER", "CUSTOMER_ADMIN"], {
      errorMap: () => ({ message: "権限を選択してください" }),
    }),
    customer_id: z.string().min(1, "顧客を選択してください"),
  });

export type UserCreateFormValues = z.infer<typeof userCreateSchema>;

export const userEditSchema = z.object({
  first_name: z.string().min(1, "名は必須です"),
  last_name: z.string().min(1, "姓は必須です"),
  email: z
    .string()
    .min(1, "メールアドレスは必須です")
    .email("有効なメールアドレスを入力してください"),
  role: z.enum(["ADMIN", "ENGINEER", "CUSTOMER_ADMIN"], {
    errorMap: () => ({ message: "権限を選択してください" }),
  }),
  customer_id: z.string().min(1, "顧客を選択してください"),
  status: z.enum(["ACTIVE", "INACTIVE"]),
});

export type UserEditFormValues = z.infer<typeof userEditSchema>;

// Schema for password setting page
export const passwordSetSchema = z.object({
  password: z.string().min(8, "パスワードは8文字以上である必要があります"),
  verify_password: z.string(),
}).refine((data) => data.password === data.verify_password, {
  message: "パスワードが一致しません",
  path: ["verify_password"],
});

export type PasswordSetFormValues = z.infer<typeof passwordSetSchema>;