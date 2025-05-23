import { z } from "zod";

export const deployToDeviceSchema = z.object({
  customer_id: z.string().min(1, "顧客を選択してください"),
  device_id: z.string().min(1, "デバイスを選択してください"),
  version_deployed: z.string().min(1, "バージョンは必須です"),
  configuration: z.any().optional(),
});

export type DeployToDeviceFormValues = z.infer<typeof deployToDeviceSchema>;