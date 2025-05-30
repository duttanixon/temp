"use client";

import { CommonFormContent } from "@/app/(main)/users/add/_components/CommonFormContent";
import { AdminFormContent } from "@/app/(main)/users/add/_components/AdminFormContent";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ApiError, userService } from "@/services/userService";
import { toast } from "sonner";
import { cva } from "class-variance-authority";
import { useEffect, useState } from "react";
import { UserCreateFormValues, userCreateSchema } from "@/schemas/userSchemas";
import { customerService } from "@/services/customerService";
import { Button } from "@/components/ui/button";

type Props = {
  role: "ADMIN" | "ENGINEER" | "CUSTOMER_ADMIN" | undefined;
};
export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      inputName: "w-75 h-10 border border-[#BDC3C7] rounded-md",
      input: "w-155 h-10 border border-[#BDC3C7] rounded-md",
      userInfo: "text-lg font-bold text-[#2C3E50]",
    },
  },
  defaultVariants: {
    variant: "userInfo",
  },
});

export default function UserCreateForm({ role }: Props) {
  const router = useRouter();

  const [customers, setCustomers] = useState<
    { name: string; customer_id: string }[]
  >([]);

  useEffect(() => {
    customerService
      .getCustomers()
      .then((data) => setCustomers(data))
      .catch((err) => {
        console.error("顧客情報の取得に失敗しました", err);
        toast.error("顧客情報の取得に失敗しました");
      });
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UserCreateFormValues>({
    resolver: zodResolver(userCreateSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      password: "",
      verify_password: "",
      role: undefined,
      status: "ACTIVE",
      customer_id: "",
    },
  });

  const onSubmit = async (data: UserCreateFormValues) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { verify_password, ...apiData } = data;
      await userService.createUser(apiData);
      toast.success("作成完了", {
        description: "新しいユーザーが正常に作成されました。",
      });
      router.push("/users");
      router.refresh();
    } catch (error) {
      console.error("Error creating user:", error);

      if (error instanceof ApiError) {
        const statusCode = error.statusCode;

        let description = "";

        switch (statusCode) {
          case 400:
            description = "このメールアドレスは既に登録されています。";
            break;
          case 403:
            description = "この操作を実行する権限がありません。";
            break;
          case 422:
            description =
              "入力内容に問題があります。必須項目を確認してください。";
            break;
          default:
            description = "予期しないエラーが発生しました。";
        }
        toast.error("作成エラー", { description });
      } else {
        toast.error("作成エラー", {
          description: "予期しないエラーが発生しました。",
        });
      }
    }
  };

  const handleFormSubmit = handleSubmit(
    (data) => {
      onSubmit(data);
    },
    (errors) => {
      console.error("Form submission error:", errors);
      if (Object.keys(errors).length > 0) {
        toast.error("基本情報に入力エラーがあります");
      }
    }
  );

  return (
    <div>
      <div className="flex flex-col gap-8">
        <form onSubmit={handleFormSubmit} className="flex flex-col gap-4">
          <div className="w-full h-145 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
            <CommonFormContent register={register} errors={errors} />
            <div className="flex gap-5">
              {role === "ADMIN" && (
                <AdminFormContent
                  register={register}
                  errors={errors}
                  customers={customers}
                />
              )}
            </div>
          </div>
          <div className="flex justify-end w-full gap-2">
            <Button
              className="w-35 bg-white border border-[#BDC3C7] text-[#7F8C8D] hover:bg-[#ECF0F1] active:bg-[#BDC3C7] hover:cursor-pointer"
              type="button"
              onClick={() => router.push("/users")}
              disabled={isSubmitting}
            >
              キャンセル
            </Button>
            <Button
              className="w-35 bg-[#27AE60] text-[#FFFFFF] hover:bg-[#219653] active:bg-[#27AE60] focus:bg-[#219653] hover:cursor-pointer"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "作成中..." : "作成"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
