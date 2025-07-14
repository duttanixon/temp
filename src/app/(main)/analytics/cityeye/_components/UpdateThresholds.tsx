import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAnalyticsDirectionPutThreshold } from "@/hooks/analytics/city_eye/useAnalyticsDirectionPutThreshold";
import {
  AnalyticsCityEyeThresholdsFormValues,
  analyticsCityEyeThresholdsSchema,
} from "@/schemas/analyticsCityEyeThresholdsSchemas";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import type { FieldErrors } from "react-hook-form";
import { toast } from "sonner";

export default function UpdateThresholds({
  solution_id,
  customer_id,
  type, // "human" | "traffic"
  Unit,
  onUpdated,
  initialThresholds,
}: {
  solution_id: string;
  customer_id: string;
  type: "human" | "traffic";
  Unit?: string;
  onUpdated?: (newThresholds: number[]) => void;
  initialThresholds?: number[];
}) {
  const [isLoading, setIsLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const { register, handleSubmit, reset, watch } = useForm({
    resolver: zodResolver(analyticsCityEyeThresholdsSchema),
    defaultValues: {
      thresholds: initialThresholds
        ? initialThresholds.map((value) => ({ value }))
        : [{ value: 0 }, { value: 0 }, { value: 0 }],
    },
  });

  // initialThresholdsの変更時に表示を更新
  useEffect(() => {
    if (initialThresholds) {
      reset({
        thresholds: initialThresholds.map((value) => ({ value })),
      });
    }
  }, [initialThresholds, reset]);

  // 閾値の順序を検証する関数
  const validateThresholdsOrder = (values: number[]): boolean => {
    for (let i = 0; i < values.length - 1; i++) {
      if (values[i] >= values[i + 1]) {
        return false;
      }
    }
    return true;
  };

  const handleDialogClose = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) {
      reset(); // モーダルが閉じられたときにフォームをリセット
    }
  };

  const onError = (
    errors: FieldErrors<AnalyticsCityEyeThresholdsFormValues>
  ) => {
    const firstError = Array.isArray(errors?.thresholds)
      ? errors.thresholds.find((e) => e?.value)
      : undefined;
    if (firstError?.value?.message) {
      toast.error(firstError.value.message);
    }
  };
  const { fetchData } = useAnalyticsDirectionPutThreshold();

  const onSubmit = async (data: AnalyticsCityEyeThresholdsFormValues) => {
    const thresholdValues = data.thresholds.map((t) => t.value);
    // 閾値の順序をチェック
    if (!validateThresholdsOrder(thresholdValues)) {
      // 閾値の順序が正しくない場合のエラーメッセージ
      toast.error("Thresholds must be in ascending order");
      return;
    }
    setIsLoading(true);
    const responseData = {
      solution_id,
      customer_id,
      thresholds:
        type === "human"
          ? {
              human_count_thresholds: thresholdValues,
            }
          : {
              traffic_count_thresholds: thresholdValues,
            },
    };
    await fetchData(responseData);
    setOpen(false);
    setIsLoading(false);
    if (onUpdated) {
      onUpdated(thresholdValues);
    }
    reset();
  };

  const values = [
    watch("thresholds.0.value"),
    watch("thresholds.1.value"),
    watch("thresholds.2.value"),
  ];
  return (
    <Dialog open={open} onOpenChange={handleDialogClose}>
      <DialogTrigger asChild>
        <Button variant="outline" className="cursor-pointer">
          閾値変更
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit, onError)} className="space-y-4">
          <DialogHeader>
            <DialogTitle>閾値を変更</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-3 items-center gap-4 pt-4">
            <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-gray-300 z-0" />
            <div className="absolute left-0 right-0 top-7/24 h-0.5 bg-gray-300 z-0" />
            <div className="absolute left-0 right-0 top-25/36 h-0.5 bg-gray-300 z-0" />

            <div className="flex flex-col justify-center items-center gap-12">
              <Label className="text-sm font-medium">少ない</Label>
              <Label className="text-sm font-medium">やや少ない</Label>
              <Label className="text-sm font-medium">やや多い</Label>
              <Label className="text-sm font-medium">多い</Label>
            </div>
            <div className="flex flex-col justify-center items-center gap-12">
              <span className="text-sm font-medium">
                {typeof values[0] === "number" && values[0] > 0
                  ? `${values[0]}${Unit}未満`
                  : "未設定"}
              </span>
              <span className="text-sm font-medium">
                {typeof values[0] === "number" &&
                values[0] > 0 &&
                typeof values[1] === "number" &&
                values[1] > 0
                  ? `${values[0]}${Unit}〜${values[1] - 1}${Unit}`
                  : "未設定"}
              </span>
              <span className="text-sm font-medium">
                {typeof values[1] === "number" &&
                values[1] > 0 &&
                typeof values[2] === "number" &&
                values[2] > 0
                  ? `${values[1]}${Unit}〜${values[2] - 1}${Unit}`
                  : "未設定"}
              </span>
              <span className="text-sm font-medium">
                {typeof values[2] === "number" && values[2] > 0
                  ? `${values[2]}${Unit}以上`
                  : "未設定"}
              </span>
            </div>
            <div className="flex flex-col justify-center items-center gap-10">
              {[0, 1, 2].map((idx) => (
                <div
                  key={idx}
                  className="flex flex-col items-center justify-center gap-4 w-full relative"
                >
                  <span className="text-xs text-gray-500 absolute left-0 right-0 top-0 -translate-y-5/4 z-0">
                    threshold
                  </span>
                  <Input
                    id={`thresholds.${idx}.value`}
                    type="input"
                    className="w-24 text-center z-10 bg-white border border-gray-300"
                    {...register(`thresholds.${idx}.value`, {
                      valueAsNumber: true,
                      required: "閾値は必須です",
                      min: {
                        value: 1,
                        message: "閾値は1以上でなければなりません",
                      },
                    })}
                  />
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button
                className="bg-white border border-[#BDC3C7] text-[#7F8C8D] hover:bg-[#ECF0F1] active:bg-[#BDC3C7] hover:cursor-pointer"
                onClick={() => reset()}
              >
                キャンセル
              </Button>
            </DialogClose>
            <Button
              type="submit"
              disabled={isLoading}
              className=" bg-[#27AE60] text-[#FFFFFF] hover:bg-[#219653] active:bg-[#27AE60] focus:bg-[#219653] hover:cursor-pointer"
            >
              {isLoading ? "更新中..." : "保存"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
