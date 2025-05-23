import { z } from "zod";

export const assignToCustomerSchema = z.object({
  customer_id: z.string().min(1, "顧客を選択してください"),
  max_devices: z.number().min(1, "最低1台のデバイスが必要です"),
  expiration_date: z.string().optional(),
  license_status: z.enum(["ACTIVE", "SUSPENDED"]),
});

export type AssignToCustomerFormValues = z.infer<typeof assignToCustomerSchema>;