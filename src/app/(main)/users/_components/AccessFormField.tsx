import { Label } from "@/components/ui/label";
import { FC } from "react";
import { cn } from "@/lib/utils";

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
  labelClassName?: string;
  inputClassName?: string;
  options?: { label: string; value: string }[];
  placeholder?: string;
};

export const AccessFormField: FC<FormFieldProps> = ({
  id,
  label,
  name,
  value,
  onChange,
  required = false,
  labelClassName = "",
  inputClassName = "",
  placeholder = "選択してください",
  options = [],
}) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={cn(labelClassName)}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>
    <select
      className={cn(inputClassName)}
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
  </div>
);
