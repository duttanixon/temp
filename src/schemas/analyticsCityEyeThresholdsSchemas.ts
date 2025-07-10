import { z } from "zod";

export const analyticsCityEyeThresholdsSchema = z.object({
  thresholds: z.array(
    z.object({
      value: z.number().min(1, "値は1以上でなければなりません"),
    })
  ),
});
export type AnalyticsCityEyeThresholdsFormValues = z.infer<
  typeof analyticsCityEyeThresholdsSchema
>;
