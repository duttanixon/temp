import { cva } from "class-variance-authority";
import { UserFormField } from "@/app/(main)/users/_components/UserFormField";

type Props = {
  userId?: string;
  status: string;
  setStatus: (val: string) => void;
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

export const AccountStatusContent = ({ status, setStatus }: Props) => {
  return (
    <>
      <div className="flex items-center gap-x-16">
        <h2 className={formVariants({ variant: "userInfo" })}>
          アカウント状態
        </h2>
      </div>
      <UserFormField
        id="status"
        label="アカウント状態"
        name="status"
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        labelClassName={formVariants({ variant: "label" })}
        inputClassName={formVariants({ variant: "inputName" })}
        as="toggle"
        options={[
          { label: "アクティブ", value: "ACTIVE" },
          { label: "非アクティブ", value: "INACTIVE" },
        ]}
      />
    </>
  );
};
