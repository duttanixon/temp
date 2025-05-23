import { cva } from "class-variance-authority";
import { UserFormField } from "@/app/(main)/users/_components/UserFormField";

type Props = {
  userId?: string;
  firstName: string;
  setFirstName: (val: string) => void;
  lastName: string;
  setLastName: (val: string) => void;
  email: string;
  setEmail: (val: string) => void;
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

export const CommonFormContent = ({
  firstName,
  setFirstName,
  lastName,
  setLastName,
  email,
  setEmail,
}: Props) => {
  return (
    <>
      <div className="flex items-center gap-x-16">
        <h2 className={formVariants({ variant: "userInfo" })}>ユーザー情報</h2>
        <span className="text-sm font-formal text-[#7F8C8D]">
          <span className="text-[#FF0000]">*</span>必須項目
        </span>
      </div>
      <div className="flex flex-col items-center gap-2">
        <div className="flex gap-5">
          <UserFormField
            id="lastName"
            label="姓"
            type="text"
            name="lastName"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "inputName" })}
          />
          <UserFormField
            id="firstName"
            label="名"
            type="text"
            name="firstName"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "inputName" })}
          />
        </div>
        <UserFormField
          id="email"
          label="メールアドレス"
          type="email"
          name="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          labelClassName={formVariants({ variant: "label" })}
          inputClassName={formVariants({ variant: "input" })}
        />
      </div>
    </>
  );
};
