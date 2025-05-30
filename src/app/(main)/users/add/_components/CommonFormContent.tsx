import { cva } from "class-variance-authority";
import { UserFormField } from "@/app/(main)/users/_components/UserFormField";

type Props = {
  register: any;
  errors: any;
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
export const CommonFormContent = ({ register, errors }: Props) => {
  return (
    <>
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
            <UserFormField
              id="last_name"
              label="姓"
              type="text"
              register={register}
              errors={errors}
              required
              labelClassName={formVariants({ variant: "label" })}
              inputClassName={formVariants({ variant: "inputName" })}
            />
            <UserFormField
              id="first_name"
              label="名"
              type="text"
              register={register}
              errors={errors}
              required
              labelClassName={formVariants({ variant: "label" })}
              inputClassName={formVariants({ variant: "inputName" })}
            />
          </div>
          <UserFormField
            id="email"
            label="連絡先メール"
            type="email"
            register={register}
            errors={errors}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "input" })}
          />
          <UserFormField
            id="password"
            label="パスワード"
            type="password"
            register={register}
            errors={errors}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "input" })}
          />
          <UserFormField
            id="verify_password"
            label="パスワード(確認用)"
            type="password"
            register={register}
            errors={errors}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "input" })}
          />
        </div>
      </div>
    </>
  );
};
