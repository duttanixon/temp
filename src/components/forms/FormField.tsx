import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import { FC } from "react";
import {
  Control,
  Controller,
  FieldErrors,
  UseFormRegister,
} from "react-hook-form";

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

// 専用のToggleFieldコンポーネント
type ToggleFieldProps = {
  id: string;
  label: string;
  control: Control<any>;
  errors?: FieldErrors;
  required?: boolean;
  activeLabel?: string;
  inactiveLabel?: string;
};

export const ToggleField: FC<ToggleFieldProps> = ({
  id,
  label,
  control,
  errors,
  required = false,
  activeLabel = "アクティブ",
  inactiveLabel = "非アクティブ",
}) => (
  <div className="flex flex-col gap-2">
    <Label className={formVariants({ variant: "label" })}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>

    <Controller
      name={id}
      control={control}
      defaultValue="INACTIVE"
      render={({ field: { onChange, value } }) => {
        const isActive = value === "ACTIVE";

        return (
          <div className="flex items-center gap-3">
            <button
              type="button"
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors hover:cursor-pointer ${
                isActive ? "bg-[#3498DB]" : "bg-[#BDC3C7]"
              }`}
              onClick={() => onChange(isActive ? "INACTIVE" : "ACTIVE")}>
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isActive ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
            <span
              className={cn(
                isActive ? "text-[#3498DB]" : "text-[#BDC3C7]",
                "text-sm"
              )}>
              {isActive ? activeLabel : inactiveLabel}
            </span>
          </div>
        );
      }}
    />

    {errors && errors[id] && (
      <div className={formVariants({ variant: "error" })}>
        {errors[id]?.message?.toString()}
      </div>
    )}
  </div>
);
