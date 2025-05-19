"use client";

import { ApiError, customerService } from "@/services/customerService";

import { FormField } from "@/components/forms/FormField";
import { Button } from "@/components/ui/button";
import {
  CustomerCreateFormValues,
  customerCreateSchema,
} from "@/schemas/customerSchemas";
import { zodResolver } from "@hookform/resolvers/zod";
import { cva } from "class-variance-authority";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      input: "w-96 h-[35.56px] border border-[#BDC3C7]",
      companyInfo: "text-lg font-bold text-[#2C3E50]",
    },
  },
  defaultVariants: {
    variant: "companyInfo",
  },
});

type CustomerCreateFormProps = {
  activeTab: string;
};

export default function CustomerCreateForm({
  activeTab,
}: CustomerCreateFormProps) {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CustomerCreateFormValues>({
    resolver: zodResolver(customerCreateSchema),
    defaultValues: {
      name: "",
      contact_email: "",
      address: "",
    },
  });

  const onSubmit = async (data: CustomerCreateFormValues) => {
    try {
      await customerService.createCustomer(data);
      toast.success("作成完了", {
        description: "新しい顧客が正常に作成されました。",
      });
      router.push("/customers");
      router.refresh();
    } catch (error) {
      console.log("Error creating customer:", error);

      if (error instanceof ApiError) {
        const statusCode = error.statusCode;

        // ステータスコードに基づいた処理
        let description = "";

        switch (statusCode) {
          case 400:
            description =
              "この会社名またはメールアドレスは既に登録されています。";
            break;
          case 403:
            description = "この操作を実行する権限がありません。";
            break;
          case 422:
            description =
              "入力内容に問題があります。必須項目を確認してください。";
            break;
          default:
            description = error.message || "予期せぬエラーが発生しました。";
        }
        toast.error("作成エラー", { description });
      } else {
        toast.error("作成エラー", {
          description:
            error instanceof Error
              ? error.message
              : "予期せぬエラーが発生しました",
        });
      }
    }
  };

  // フォーム送信前にエラーがあるか確認するハンドラーを追加
  const handleFormSubmit = handleSubmit(
    (data) => {
      onSubmit(data);
    },
    (errors) => {
      // バリデーションエラーがあり、かつサブスクリプションタブが選択されている場合
      if (Object.keys(errors).length > 0 && activeTab !== "basic") {
        toast.error("基本情報に入力エラーがあります", {
          description: "「基本情報」タブに戻り、必須項目を入力してください。",
        });
      }
    }
  );

  return (
    <form onSubmit={handleFormSubmit} className="flex flex-col gap-4">
      <div className="w-230 h-106 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
        {/* activeTabが'basic'の場合、空のdivを表示し、'subscription'ならサンプルtextを表示 */}
        {activeTab === "basic" ? (
          <div className="flex flex-col gap-4 p-4">
            <div className="flex items-center gap-x-16">
              <h2 className={formVariants({ variant: "companyInfo" })}>
                会社情報
              </h2>
              <span className="text-sm font-normal text-[#7F8C8D]">
                <span className="text-[#FF0000]">*</span> 必須項目
              </span>
            </div>
            <div className="w-96 flex flex-col gap-2">
              <FormField
                id="name"
                label="会社名"
                type="text"
                register={register}
                errors={errors}
                required
              />
              <FormField
                id="contact_email"
                label="メールアドレス"
                type="email"
                register={register}
                errors={errors}
                required
              />
              <FormField
                id="address"
                label="住所"
                type="text"
                register={register}
                errors={errors}
              />
            </div>
          </div>
        ) : (
          <div className="p-4">
            <span className="text-lg font-bold text-[#2C3E50]">
              サブスクリプション
            </span>
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <Button
          className="w-35 bg-[#27AE60] text-[#FFFFFF] hover:bg-[#219653] active:bg-[#27AE60] focus:bg-[#219653] hover:cursor-pointer"
          type="submit"
          disabled={isSubmitting}>
          {isSubmitting ? "作成中..." : "作成"}
        </Button>
        <Button
          className="w-35 bg-[#BDC3C7] text-[#7F8C8D] hover:bg-[#A6ACAF] active:bg-[#BDC3C7] focus:bg-[#A6ACAF] hover:cursor-pointer"
          type="button"
          onClick={() => router.push("/customers")}
          disabled={isSubmitting}>
          キャンセル
        </Button>
      </div>
    </form>
  );
}
