"use client";

import { CommonFormContent } from "@/app/(main)/users/[id]/edit/_components/CommonFormContent";
import { AccessControlContent } from "@/app/(main)/users/[id]/edit/_components/AccessControlContent";
import { User } from "@/types/user";
import { userService, ApiError } from "@/services/userService";
import { useRouter } from "next/navigation";

import { toast } from "sonner";
import { UserEditFormValues, userEditSchema } from "@/schemas/userSchemas";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { customerService } from "@/services/customerService";
import { AccountControlContent } from "@/app/(main)/users/[id]/edit/_components/AccountControlContent";

type Props = {
  role: string | undefined;
  user: User;
};
export default function UserEditForm({ role, user }: Props) {
  const router = useRouter();
  const [customers, setCustomers] = useState<
    { name: string; customer_id: string }[]
  >([]);
  const userId = user?.user_id;
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
    control,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<UserEditFormValues>({
    resolver: zodResolver(userEditSchema),
    defaultValues: {
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      email: user.email || "",
      role: ["ADMIN", "ENGINEER", "CUSTOMER_ADMIN"].includes(user.role ?? "")
        ? (user.role as "ADMIN" | "ENGINEER" | "CUSTOMER_ADMIN")
        : undefined,
      customer_id: user.customer_id || "",
      status:
        user.status === "ACTIVE" || user.status === "INACTIVE"
          ? user.status
          : "ACTIVE",
    },
  });
  useEffect(() => {
    if (
      user?.customer_id &&
      customers.some((c) => c.customer_id === user?.customer_id)
    ) {
      setValue("customer_id", user?.customer_id);
    }
  }, [user?.customer_id, customers, setValue]);

  const onSubmit = async (data: UserEditFormValues) => {
    const sanitizedData = {
      ...data,
      customer_id: data.customer_id === "none" ? undefined : data.customer_id,
    };
    try {
      await userService.updateUser(userId ?? "", sanitizedData);
      toast.success("更新完了", {
        description: "ユーザー情報が更新されました",
      });
      router.push("/users");
    } catch (error) {
      console.error("Error updating user:", error);

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
        toast.error("更新エラー", { description });
      } else {
        toast.error("更新エラー", {
          description:
            error instanceof Error
              ? error.message
              : "予期しないエラーが発生しました",
        });
      }
    }
  };

  const handleFormSubmit = handleSubmit(
    (data) => {
      onSubmit(data);
    },
    (errors) => {
      if (Object.keys(errors).length > 0) {
        toast.error("入力エラーがあります");
      }
    }
  );
  return (
    <div className="flex flex-col gap-8">
      <form onSubmit={handleFormSubmit} className="flex flex-col gap-4">
        <div className="w-full h-145 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
          <div className="flex flex-col gap-4 p-4">
            <CommonFormContent register={register} errors={errors} />
            {role === "ADMIN" && (
              <AccessControlContent
                register={register}
                errors={errors}
                customers={customers}
              />
            )}
            <AccountControlContent control={control} />
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
            {isSubmitting ? "保存中..." : "保存"}
          </Button>
        </div>
      </form>
    </div>
  );
}
