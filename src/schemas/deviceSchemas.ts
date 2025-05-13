import { z } from "zod";

// Schema for device update
export const deviceUpdateSchema = z.object({
  description: z.string().optional(),
  location: z.string().optional(),
  firmware_version: z.string().optional(),
  ip_address: z.string().optional().or(z.literal("")),
});

export type DeviceUpdateFormValues = z.infer<typeof deviceUpdateSchema>;

// Schema for device creation
export const deviceCreateSchema = z.object({
    customer_id: z.string().optional().or(z.literal("")),
    device_type: z.enum(["NVIDIA_JETSON", "RASPBERRY_PI"], {
      required_error: "デバイスタイプを選択してください",
    }),
    description: z.string().optional(),
    mac_address: z.string().optional().or(z.literal("")),
    serial_number: z.string().optional().or(z.literal("")),
    firmware_version: z.string().optional().or(z.literal("")),
    location: z.string().optional().or(z.literal("")),
    ip_address: z.string().optional().or(z.literal("")),
  });

  export type DeviceCreateFormValues = z.infer<typeof deviceCreateSchema>;