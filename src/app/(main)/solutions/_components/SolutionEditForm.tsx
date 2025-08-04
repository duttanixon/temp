"use client";

import { FormField } from "@/components/forms/FormField";
import {
  SolutionUpdateFormValues,
  solutionUpdateSchema,
} from "@/schemas/solutionSchemas";
import { solutionService } from "@/services/solutionService";
import { Solution } from "@/types/solution";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

type SolutionEditFormProps = {
  solution: Solution;
};

export default function SolutionEditForm({ solution }: SolutionEditFormProps) {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<SolutionUpdateFormValues>({
    resolver: zodResolver(solutionUpdateSchema),
    defaultValues: {
      name: solution.name,
      description: solution.description || "",
      version: solution.version,
      compatibility: solution.compatibility || [],
      status: solution.status,
    },
  });

  const onSubmit = async (data: SolutionUpdateFormValues) => {
    try {
      await solutionService.updateSolution(solution.solution_id, data);

      toast.success("ソリューションが更新されました", {
        description: `ソリューション「${solution.name}」の情報が正常に更新されました。`,
      });

      router.push(`/solutions/${solution.solution_id}/details`);
      router.refresh();
    } catch (error) {
      console.error("Error updating solution:", error);
      toast.error("更新エラー", {
        description:
          error instanceof Error
            ? error.message
            : "予期せぬエラーが発生しました",
      });
    }
  };

  const deviceTypes = [
    { id: "NVIDIA_JETSON", name: "NVIDIA Jetson" },
    { id: "RASPBERRY_PI", name: "Raspberry Pi" },
  ];

  return (
    <div className="bg-white rounded-lg border border-[#BDC3C7] overflow-hidden">
      <div className="px-6 py-4 border-b border-[#BDC3C7]">
        <h2 className="text-lg font-semibold text-[#2C3E50]">
          ソリューション情報を編集
        </h2>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            id="name"
            label="ソリューション名"
            type="text"
            register={register}
            errors={errors}
            required
          />

          <FormField
            id="version"
            label="バージョン"
            type="text"
            register={register}
            errors={errors}
            required
          />

          <div className="flex flex-col gap-1 md:col-span-2">
            <label
              htmlFor="compatibility"
              className="text-sm font-normal text-[#7F8C8D]"
            >
              互換デバイスタイプ
            </label>
            <div className="space-y-2">
              <Controller
                name="compatibility"
                control={control}
                render={({ field }) => (
                  <div className="flex flex-wrap gap-4">
                    {deviceTypes.map((type) => (
                      <label key={type.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          value={type.id}
                          onChange={(e) => {
                            const currentCompatibility = field.value || [];
                            const optionId = type.id;
                            if (e.target.checked) {
                              field.onChange([
                                ...currentCompatibility,
                                optionId,
                              ]);
                            } else {
                              field.onChange(
                                currentCompatibility.filter(
                                  (v: string) => v !== optionId
                                )
                              );
                            }
                          }}
                          checked={field.value?.includes(type.id)}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">{type.name}</span>
                      </label>
                    ))}
                  </div>
                )}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1 md:col-span-2">
            <label
              htmlFor="status"
              className="text-sm font-normal text-[#7F8C8D]"
            >
              ステータス
            </label>
            <select
              id="status"
              {...register("status")}
              className="w-full h-[35.56px] border border-[#BDC3C7] rounded"
            >
              <option value="ACTIVE">有効</option>
              <option value="BETA">ベータ版</option>
              <option value="DEPRECATED">非推奨</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <FormField
              id="description"
              label="説明"
              type="text"
              register={register}
              errors={errors}
              as="textarea"
              rows={3}
              placeholder="ソリューションの説明を入力してください"
            />
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-[#BDC3C7] rounded-md text-sm text-[#7F8C8D] hover:bg-[#ECF0F1]"
            disabled={isSubmitting}
          >
            キャンセル
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-[#27AE60] text-white rounded-md text-sm hover:bg-[#219955]"
            disabled={isSubmitting}
          >
            {isSubmitting ? "更新中..." : "保存"}
          </button>
        </div>
      </form>
    </div>
  );
}
