import { z } from "zod";

export const analyticsCityEyeThresholdsSchema = z.object({
  thresholds: z.array(
    z.object({
      value: z.number().min(1).max(99999),
    })
  ),
});
export type AnalyticsCityEyeThresholdsFormValues = z.infer<
  typeof analyticsCityEyeThresholdsSchema
>;
