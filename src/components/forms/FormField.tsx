import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cva } from "class-variance-authority";
import { FC } from "react";
import { FieldErrors, UseFormRegister } from "react-hook-form";

// Form field styling variants
export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      input: "w-full h-[35.56px] border border-[#BDC3C7]",
      error: "text-xs text-red-500 mt-1",
    },
  },
  defaultVariants: {
    variant: "label",
  },
});

type FormFieldProps = {
  id: string;
  label: string;
  type: string;
  // Make it work with react-hook-form
  register: UseFormRegister<any>;
  errors?: FieldErrors;
  required?: boolean;
  placeholder?: string;
  // Optional textarea props
  isTextarea?: boolean;
  rows?: number;
};

export const FormField: FC<FormFieldProps> = ({
  id,
  label,
  type,
  register,
  errors,
  required = false,
  placeholder = "",
  isTextarea = false,
  rows = 3,
}) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={formVariants({ variant: "label" })}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>

    {isTextarea ? (
      <textarea
        className={
          formVariants({ variant: "input" }) + " min-h-[80px] py-2 px-3"
        }
        id={id}
        rows={rows}
        placeholder={placeholder}
        {...register(id)}
      />
    ) : (
      <Input
        className={formVariants({ variant: "input" })}
        id={id}
        type={type}
        placeholder={placeholder}
        {...register(id)}
      />
    )}

    {errors && errors[id] && (
      <div className={formVariants({ variant: "error" })}>
        {errors[id]?.message?.toString()}
      </div>
    )}
  </div>
);
