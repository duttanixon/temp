import { cva } from "class-variance-authority";
import { UserFormField } from "@/app/(main)/users/_components/UserFormField";

type Props = {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  verifyPassword: string;
  setFirstName: (val: string) => void;
  setLastName: (val: string) => void;
  setEmail: (val: string) => void;
  setPassword: (val: string) => void;
  setVerifyPassword: (val: string) => void;
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
export const CommonFormContent = ({
  firstName,
  setFirstName,
  lastName,
  setLastName,
  email,
  setEmail,
  password,
  setPassword,
  verifyPassword,
  setVerifyPassword,
}: Props) => {
  return (
    <>
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-center gap-x-16 pb-5">
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
            label="連絡先メール"
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "input" })}
          />
          <UserFormField
            id="password"
            label="パスワード"
            type="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "input" })}
          />
          <UserFormField
            id="password"
            label="パスワード(確認用)"
            type="password"
            name="password"
            value={verifyPassword}
            onChange={(e) => setVerifyPassword(e.target.value)}
            required
            labelClassName={formVariants({ variant: "label" })}
            inputClassName={formVariants({ variant: "input" })}
          />
        </div>
      </div>
    </>
  );
};
