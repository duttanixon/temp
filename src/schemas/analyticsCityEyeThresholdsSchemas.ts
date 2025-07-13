import { z } from "zod";

export const analyticsCityEyeThresholdsSchema = z.object({
  thresholds: z.array(
    z.object({
      value: z.number(),
    })
  ),
});
export type AnalyticsCityEyeThresholdsFormValues = z.infer<
  typeof analyticsCityEyeThresholdsSchema
>;
