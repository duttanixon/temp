"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useForm, Controller, SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { solutionService } from "@/services/solutionService";
import {
  SolutionCreateFormValues,
  SolutionCreateFormInput,
  solutionCreateSchema,
} from "@/schemas/solutionSchemas";
import { FormField } from "@/components/forms/FormField";

export default function SolutionCreateForm() {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<SolutionCreateFormInput, any, SolutionCreateFormValues>({
    resolver: zodResolver(solutionCreateSchema),
    defaultValues: {
      name: "",
      description: "",
      version: "",
      compatibility: [],
      status: "ACTIVE",
    },
  });

  const onSubmit: SubmitHandler<SolutionCreateFormValues> = async (data) => {
    try {
      await solutionService.createSolution(data);

      toast.success("ソリューションが作成されました", {
        description: "新しいソリューションが正常に作成されました。",
      });

      router.push("/solutions");
      router.refresh();
    } catch (error) {
      console.error("Error creating solution:", error);
      toast.error("作成エラー", {
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
          新規ソリューション情報
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
            placeholder="例: 1.0.0"
          />

          <div className="flex flex-col gap-1 md:col-span-2">
            <label
              htmlFor="compatibility"
              className="text-sm font-normal text-[#7F8C8D]"
            >
              互換デバイスタイプ <span className="text-[#FF0000]">*</span>
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
                            const value = type.id;
                            if (e.target.checked) {
                              field.onChange([...field.value, value]);
                            } else {
                              field.onChange(
                                field.value.filter((v: string) => v !== value)
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
              {errors.compatibility && (
                <p className="text-xs text-red-500">
                  {errors.compatibility.message}
                </p>
              )}
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
              isTextarea={true}
              rows={3}
              placeholder="ソリューションの説明を入力してください"
            />
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.push("/solutions")}
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
            {isSubmitting ? "作成中..." : "作成"}
          </button>
        </div>
      </form>
    </div>
  );
}