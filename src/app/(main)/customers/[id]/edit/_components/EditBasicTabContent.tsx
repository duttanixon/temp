import { Input } from "@components/ui/input";
import { Label } from "@components/ui/label";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

type Props = {
  customerId?: string;
  companyName: string;
  setCompanyName: (val: string) => void;
  email: string;
  setEmail: (val: string) => void;
  address: string;
  setAddress: (val: string) => void;
  status: string;
  setStatus: (val: string) => void;
};

type FormFieldProps<
  T extends HTMLInputElement | HTMLSelectElement = HTMLInputElement,
> = {
  id: string;
  label: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<T>) => void;
  required?: boolean;
  as?: "input" | "toggle";
  options?: { label: string; value: string }[];
  type?: string;
};

export const FormField = <
  T extends HTMLInputElement | HTMLSelectElement = HTMLInputElement,
>({
  id,
  label,
  name,
  value,
  onChange,
  required = false,
  as = "input",
  type = "text",
}: FormFieldProps<T>) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={formVariants({ variant: "label" })}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>
    {as === "input" && (
      <Input
        className={formVariants({ variant: "input" })}
        id={id}
        type={type}
        name={name}
        value={value}
        onChange={onChange as (e: React.ChangeEvent<HTMLInputElement>) => void}
        required={required}
      />
    )}
    {as === "toggle" && (
      <div className="flex items-center gap-3">
        <label className="relative inline-block w-12 h-6">
          <input
            type="checkbox"
            name={name}
            checked={value === "ACTIVE"}
            onChange={(e) => {
              const syntheticEvent = {
                target: {
                  name,
                  value: e.target.checked ? "ACTIVE" : "INACTIVE",
                },
              } as unknown as React.ChangeEvent<T>;
              onChange(syntheticEvent);
            }}
            className="opacity-0"
          />
          <span className="toggle-track" />
        </label>
        <span
          className={cn(
            "text-sm",
            value === "ACTIVE" ? "text-[#3498DB]" : "text-[#BDC3C7]"
          )}
        >
          {value === "ACTIVE" ? "アクティブ" : "非アクティブ"}
        </span>
      </div>
    )}
  </div>
);

export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      input: "w-96 h-[35.56px] border border-[#BDC3C7] text-sm",
      companyInfo: "text-lg font-bold text-[#2C3E50]",
    },
  },
  defaultVariants: {
    variant: "companyInfo",
  },
});

export const EditBasicTabContent = ({
  companyName,
  setCompanyName,
  email,
  setEmail,
  address,
  setAddress,
  status,
  setStatus,
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
          label="連絡先メールアドレス"
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
        <FormField
          id="status"
          label="アカウント状態"
          name="status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          as="toggle"
          options={[
            { label: "アクティブ", value: "ACTIVE" },
            { label: "非アクティブ", value: "INACTIVE" },
          ]}
        />
      </div>
    </div>
  );
};
