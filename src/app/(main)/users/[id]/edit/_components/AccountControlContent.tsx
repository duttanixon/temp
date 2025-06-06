import { cva } from "class-variance-authority";
import { ToggleField } from "@/components/forms/FormField";
import { Control } from "react-hook-form";
import { UserEditFormValues } from "@/schemas/userSchemas";

type Props = {
  control: Control<UserEditFormValues>;
};

export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      input: "w-155 h-10 border border-[#BDC3C7] rounded-md",
      inputName: "w-75 h-10 border border-[#BDC3C7] rounded-md",
      userInfo: "text-lg font-bold text-[#2C3E50]",
    },
  },
  defaultVariants: {
    variant: "userInfo",
  },
});

export const AccountControlContent = ({ control }: Props) => {
  return (
    <>
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
    </>
  );
};
