import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { cva } from "class-variance-authority";
import { FC } from "react";

type Props = {
  companyName: string;
  setCompanyName: (val: string) => void;
  email: string;
  setEmail: (val: string) => void;
  address: string;
  setAddress: (val: string) => void;
};

type FormFieldProps = {
  id: string;
  label: string;
  type: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
};

export const FormField: FC<FormFieldProps> = ({
  id,
  label,
  type,
  name,
  value,
  onChange,
  required = false,
}) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={formVariants({ variant: "label" })}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>
    <Input
      className={formVariants({ variant: "input" })}
      id={id}
      type={type}
      name={name}
      value={value}
      onChange={onChange}
      required={required}
    />
  </div>
);

export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      input: "w-96 h-[35.56px] border border-[#BDC3C7]",
      companyInfo: "text-lg font-bold text-[#2C3E50]",
    },
  },
  defaultVariants: {
    variant: "companyInfo",
  },
});

export const AddBasicTabContent = ({
  companyName,
  setCompanyName,
  email,
  setEmail,
  address,
  setAddress,
}: Props) => {
  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex items-center gap-x-16">
        <h2 className={formVariants({ variant: "companyInfo" })}>会社情報</h2>
        <span className="text-sm font-normal text-[#7F8C8D]">
          <span className="text-[#FF0000]">*</span> 必須項目
        </span>
      </div>
      <div className="flex flex-col gap-2">
        <FormField
          id="companyName"
          label="会社名"
          type="text"
          name="companyName"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          required
        />
        <FormField
          id="email"
          label="メールアドレス"
          type="email"
          name="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <FormField
          id="address"
          label="住所"
          type="text"
          name="address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
      </div>
    </div>
  );
};
