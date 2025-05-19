import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cva } from "class-variance-authority";
import { FC } from "react";

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
type FormFieldProps = {
  id: string;
  label: string;
  type: string;
  name: string;
  value: string;
  onChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => void;
  required?: boolean;
  inputVariant?: VariantType;
  options?: { label: string; value: string }[];
  placeholder?: string;
};

type VariantType = "input" | "label" | "inputName" | "userInfo";

export const UserFormField: FC<FormFieldProps> = ({
  id,
  label,
  type,
  name,
  value,
  onChange,
  required = false,
  inputVariant = "input",
  placeholder = "選択",
  options = [],
}) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={formVariants({ variant: "label" })}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>
    {type === "select" ? (
      <select
        className={formVariants({ variant: inputVariant })}
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        required={required}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    ) : (
      <Input
        className={formVariants({ variant: inputVariant })}
        id={id}
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        required={required}
      />
    )}
  </div>
);

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
              inputVariant="inputName"
            />
            <UserFormField
              id="firstName"
              label="名"
              type="text"
              name="firstName"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
              inputVariant="inputName"
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
            inputVariant="input"
          />
          <UserFormField
            id="password"
            label="パスワード"
            type="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            inputVariant="input"
          />
          <UserFormField
            id="password"
            label="パスワード(確認用)"
            type="password"
            name="password"
            value={verifyPassword}
            onChange={(e) => setVerifyPassword(e.target.value)}
            required
            inputVariant="input"
          />
        </div>
      </div>
    </>
  );
};
