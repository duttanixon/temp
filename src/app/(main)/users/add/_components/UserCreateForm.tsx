"use client";

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
import { UserRole } from "@/types/user";
import { FormField } from "@/components/forms/FormField";

type Props = {
  role: UserRole;
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
        toast.error("入力エラーがあります");
      }
    }
  );

  return (
    <form onSubmit={handleFormSubmit} className="flex flex-col gap-4">
      <div className="w-full h-145 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
        <div className="flex flex-col gap-4 p-4">
          <div className="flex items-center gap-x-16">
            <h2 className={formVariants({ variant: "userInfo" })}>
              ユーザー情報
            </h2>
            <span className="text-sm font-normal text-[#7F8C8D]">
              <span className="text-[#FF0000]">*</span> 必須項目
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
              label="連絡先メール"
              type="email"
              register={register}
              errors={errors}
              required
              as="input"
              inputClassName={formVariants({ variant: "input" })}
            />
            <FormField
              id="password"
              label="パスワード"
              type="password"
              register={register}
              errors={errors}
              required
              as="input"
              inputClassName={formVariants({ variant: "input" })}
            />
            <FormField
              id="verify_password"
              label="パスワード(確認用)"
              type="password"
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
              <span className="text-sm font-normal text-[#7F8C8D]">
                <span className="text-[#FF0000]">*</span> 必須項目
              </span>
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
                  placeholder="選択してください(任意)"
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
  );
}
