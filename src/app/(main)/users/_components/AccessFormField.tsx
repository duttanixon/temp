import { Label } from "@/components/ui/label";
import { FC } from "react";
import { cn } from "@/lib/utils";
import { FieldErrors, UseFormRegister } from "react-hook-form";
import { formVariants } from "@/components/forms/FormField";

type AccessFormFieldProps = {
  id: string;
  label: string;
  type: string;
  register: UseFormRegister<any>;
  errors?: FieldErrors;
  required?: boolean;
  labelClassName?: string;
  inputClassName?: string;
  options?: { label: string; value: string }[];
  placeholder?: string;
};

export const AccessFormField: FC<AccessFormFieldProps> = ({
  id,
  label,
  register,
  errors,
  required = false,
  labelClassName = "",
  inputClassName = "",
  placeholder = "",
  options = [],
}) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={cn(labelClassName)}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>
    <select
      className={cn(inputClassName)}
      id={id}
      {...register(id)}
      required={required}
    >
      <option value="">{placeholder}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
    {errors && errors[id] && (
      <div className={formVariants({ variant: "error" })}>
        {errors[id]?.message?.toString()}
      </div>
    )}
  </div>
);
