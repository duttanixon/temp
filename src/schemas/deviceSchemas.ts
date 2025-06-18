import { z } from "zod";

// Schema for device update
export const deviceUpdateSchema = z.object({
  description: z.string().optional(),
  location: z.string().optional(),
  firmware_version: z.string().optional(),
  ip_address: z.string().optional().or(z.literal("")),
//   latitude: z.preprocess(
//     (val) => (val === "" ? undefined : Number(val)),
//     z.number({ invalid_type_error: "有効な数値を入力してください" })
//       .min(-90, { message: "緯度は-90以上でなければなりません" })
//       .max(90, { message: "緯度は90以内でなければなりません" })
//       .optional()
//   ),
//   longitude: z.preprocess(
//     (val) => (val === "" ? undefined : Number(val)),
//     z.number({ invalid_type_error: "有効な数値を入力してください" })
//       .min(-180, { message: "経度は-180以上でなければなりません" })
//       .max(180, { message: "経度は180以内でなければなりません" })
//       .optional()
//   ),
latitude: z.preprocess(
  (val) => {
    if (val === "" || val === null || val === undefined) return null;
    const num = Number(val);
    return isNaN(num) ? null : num;
  },
  z.number({ invalid_type_error: "有効な数値を入力してください" })
    .min(-90, { message: "緯度は-90以上でなければなりません" })
    .max(90, { message: "緯度は90以内でなければなりません" })
    .nullable()
    .optional()
),
longitude: z.preprocess(
  (val) => {
    if (val === "" || val === null || val === undefined) return null;
    const num = Number(val);
    return isNaN(num) ? null : num;
  },
  z.number({ invalid_type_error: "有効な数値を入力してください" })
    .min(-180, { message: "経度は-180以上でなければなりません" })
    .max(180, { message: "経度は180以内でなければなりません" })
    .nullable()
    .optional()
),
});

// EXPORT BOTH THE INPUT AND OUTPUT (INFER) TYPES
export type DeviceUpdateFormInput = z.input<typeof deviceUpdateSchema>;
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