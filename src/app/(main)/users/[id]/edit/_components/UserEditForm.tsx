"use client";

import { cva } from "class-variance-authority";
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
import { FormField } from "@/components/forms/FormField";
import { ToggleField } from "@/components/forms/FormField";

type Props = {
  role: string | undefined;
  user: User;
};
export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      halfInput: "w-75 h-10 border border-[#BDC3C7] text-sm rounded-md",
      input: "w-155 h-10 border border-[#BDC3C7] rounded-md",
      userInfo: "text-lg font-bold text-[#2C3E50]",
    },
  },
  defaultVariants: {
    variant: "userInfo",
  },
});

export default function UserEditForm({ role, user }: Props) {
  const router = useRouter();
  const [customers, setCustomers] = useState<
    { name: string; customer_id: string }[]
  >([]);
  const userId = user?.user_id;

  useEffect(() => {
    if (role === "ADMIN") {
      customerService
        .getCustomers()
        .then((data) => setCustomers(data))
        .catch((err) => {
          console.error("顧客情報の取得に失敗しました", err);
          toast.error("顧客情報の取得に失敗しました");
        });
    }
  }, [role]);

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
    try {
      if (data.role === "ADMIN") {
        const confirmation = window.confirm(
          "システム管理者権限のユーザーを更新します。\nこのまま更新してもよろしいですか？"
        );
        if (!confirmation) {
          return;
        }
      }
      const sanitizedData = {
        ...data,
        customer_id: data.customer_id === "none" ? undefined : data.customer_id,
      };
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
    <form onSubmit={handleFormSubmit} className="flex flex-col gap-4">
      <div className="w-full pb-4 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
        <div className="flex flex-col gap-4 p-4">
          <div className="flex items-center gap-x-16">
            <h2 className={formVariants({ variant: "userInfo" })}>
              ユーザー情報
            </h2>
            <span className="text-sm font-formal text-[#7F8C8D]">
              <span className="text-[#FF0000]">*</span>必須項目
            </span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="flex gap-5">
              <FormField
                id="last_name"
                label="姓"
                type="text"
                register={register}
                errors={errors}
                required
                as="input"
                inputClassName={formVariants({ variant: "halfInput" })}
              />
              <FormField
                id="first_name"
                label="名"
                type="text"
                register={register}
                errors={errors}
                required
                as="input"
                inputClassName={formVariants({ variant: "halfInput" })}
              />
            </div>
            <FormField
              id="email"
              label="メールアドレス"
              type="email"
              register={register}
              errors={errors}
              required
              as="input"
              inputClassName={formVariants({ variant: "input" })}
            />
          </div>
        </div>
        {role === "ADMIN" && (
          <div className="flex flex-col gap-4 p-4">
            <div className="flex items-center gap-x-16">
              <h2 className={formVariants({ variant: "userInfo" })}>
                アクセス制御
              </h2>
              <span className="text-sm font-normal text-[#7F8C8D]"></span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="flex gap-5">
                <FormField
                  id="customer_id"
                  label="顧客"
                  as="select"
                  register={register}
                  errors={errors}
                  required
                  inputClassName={formVariants({ variant: "halfInput" })}
                  placeholder="選択してください"
                  options={[
                    ...customers.map(
                      (customer: { name: string; customer_id: string }) => ({
                        label: customer.name,
                        value: customer.customer_id,
                      })
                    ),
                  ]}
                />
                <FormField
                  id="role"
                  label="権限"
                  as="select"
                  register={register}
                  errors={errors}
                  required
                  inputClassName={formVariants({ variant: "halfInput" })}
                  placeholder="選択してください"
                  options={[
                    { label: "システム管理者", value: "ADMIN" },
                    { label: "エンジニア", value: "ENGINEER" },
                    { label: "顧客", value: "CUSTOMER_ADMIN" },
                  ]}
                />
              </div>
            </div>
          </div>
        )}
        <div className="flex flex-col gap-4 p-4">
          <div className="flex items-center gap-x-16">
            <h2 className={formVariants({ variant: "userInfo" })}>
              アカウント制御
            </h2>
          </div>
          <ToggleField
            id="status"
            label="状態"
            control={control}
            activeLabel="アクティブ"
            inactiveLabel="非アクティブ"
          />
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
  );
}
