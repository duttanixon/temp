import { FormField, ToggleField } from "@/components/forms/FormField";
import { Button } from "@/components/ui/button";
import {
  CustomerEditFormValues,
  customerEditSchema,
} from "@/schemas/customerSchemas";
import { ApiError, customerService } from "@/services/customerService";
import { Customer } from "@/types/customer";
import { zodResolver } from "@hookform/resolvers/zod";
import { cva } from "class-variance-authority";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      input: "w-96 h-[35.56px] border border-[#BDC3C7] text-sm",
      companyInfo: "text-lg font-bold text-[#2C3E50]",
    },
  },
  defaultVariants: {
    variant: "companyInfo",
  },
});

const buttonVariants = cva("w-35 text-sm font-normal cursor-pointer", {
  variants: {
    variant: {
      default:
        "bg-[#27AE60] text-[#FFFFFF] hover:bg-[#219653] active:bg-[#27AE60] focus:bg-[#219653]",
      cancel:
        "bg-[#BDC3C7] text-[#7F8C8D] hover:bg-[#A6ACAF] active:bg-[#BDC3C7] focus:bg-[#A6ACAF]",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export default function CustomerEditForm({
  activeTab,
  customer,
}: {
  activeTab: string;
  customer: Customer;
}) {
  const router = useRouter();

  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CustomerEditFormValues>({
    resolver: zodResolver(customerEditSchema),
    defaultValues: {
      name: customer.name || "",
      contact_email: customer.contact_email || "",
      address: customer.address || "",
      status: customer.status || "ACTIVE",
    },
  });
  const customerId = customer.customer_id;

  const onSubmit = async (data: CustomerEditFormValues) => {
    try {
      await customerService.updateCustomer(customerId, data);
      toast.success("更新完了", {
        description: "顧客情報が更新されました。",
      });
      router.push(`/customers/${customerId}`);
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
        toast.error("更新エラー", { description });
      } else {
        toast.error("更新エラー", {
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
                type="contact_email"
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
              {/* 専用のトグルスイッチコンポーネント */}
              <ToggleField
                id="status"
                label="アカウント状態"
                control={control}
                activeLabel="アクティブ"
                inactiveLabel="非アクティブ"
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
          className={buttonVariants({ variant: "default" })}
          type="submit"
          disabled={isSubmitting}>
          {isSubmitting ? "保存中..." : "保存"}
        </Button>
        <Button
          className={buttonVariants({ variant: "cancel" })}
          type="button"
          onClick={() => router.push(`/customers/${customerId}`)}
          disabled={isSubmitting}>
          キャンセル
        </Button>
      </div>
    </form>
  );
}
