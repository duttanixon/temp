import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { FC } from "react";
import { FieldErrors, UseFormRegister } from "react-hook-form";
import { formVariants } from "@/components/forms/FormField";

type UserFormFieldProps = {
  id: string;
  label: string;
  type: string;
  register: UseFormRegister<any>;
  errors?: FieldErrors;
  required?: boolean;
  labelClassName?: string;
  inputClassName?: string;
  as?: "input" | "toggle";
  options?: { label: string; value: string }[];
  placeholder?: string;
};

export const UserFormField: FC<UserFormFieldProps> = ({
  id,
  label,
  register,
  errors,
  required = false,
  labelClassName = "",
  inputClassName = "",
  as = "input",
  type = "text",
  placeholder = "",
}) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={cn(labelClassName)}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>
    {as === "input" && (
      <Input
        className={cn(inputClassName)}
        id={id}
        type={type}
        {...register(id)}
        required={required}
        placeholder={placeholder}
      />
    )}
    {as === "toggle" && (
      <div className="flex items-center gap-3">
        <label className="relative inline-block w-12 h-6">
          <input type="checkbox" id={id} className="opacity-0" />
          <span className="toggle-track" />
        </label>
        <span className={cn("text-sm")}></span>
      </div>
    )}
    {errors && errors[id] && (
      <div className={formVariants({ variant: "error" })}>
        {errors[id]?.message?.toString()}
      </div>
    )}
  </div>
);
