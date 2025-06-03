import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import { FC } from "react";
import {
  Control,
  Controller,
  FieldErrors,
  FieldValues,
  Path,
  UseFormRegister,
} from "react-hook-form";

// Form field styling variants
export const formVariants = cva("", {
  variants: {
    variant: {
      label: "text-sm font-normal text-[#7F8C8D]",
      input: "w-full h-[35.56px] border border-[#BDC3C7]",
      halfInput: "w-1/2 h-[35.56px] border border-[#BDC3C7]",
      error: "text-xs text-red-500 mt-1",
    },
  },
  defaultVariants: {
    variant: "label",
  },
});

type FormFieldProps<TFieldValues extends FieldValues> = {
  id: Path<TFieldValues>;
  label: string;
  // Make it work with react-hook-form
  register: UseFormRegister<TFieldValues>;
  errors?: FieldErrors<TFieldValues>;
  required?: boolean;
  placeholder?: string;
  labelClassName?: string;
  inputClassName?: string;
  // Optional textarea props
  as?: "input" | "textarea" | "select";
  type?: string;
  rows?: number;
  options?: {
    label: string;
    value: string | number | readonly string[] | undefined;
  }[];
};

export const FormField = <TFieldValues extends FieldValues>({
  id,
  label,
  register,
  errors,
  required = false,
  placeholder = "",
  inputClassName = "",
  labelClassName = "",
  as = "input",
  type = "text",
  rows = 3,
  options = [],
}: FormFieldProps<TFieldValues>) => (
  <div className="flex flex-col gap-1">
    <Label
      htmlFor={id}
      className={cn(formVariants({ variant: "label" }), labelClassName)}
    >
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>

    {as === "input" && (
      <Input
        className={cn(formVariants({ variant: "input" }), inputClassName)}
        id={id}
        type={type}
        placeholder={placeholder}
        {...register(id)}
      />
    )}
    {as === "textarea" && (
      <textarea
        className={cn(
          formVariants({ variant: "input" }),
          inputClassName,
          "min-h-[80px] py-2 px-3"
        )}
        id={id}
        rows={rows}
        placeholder={placeholder}
        {...register(id)}
      />
    )}
    {as === "select" && (
      <select
        className={cn(formVariants({ variant: "input" }), inputClassName)}
        id={id}
        {...register(id)}
        required={required}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value?.toString()} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
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
              onClick={() => onChange(isActive ? "INACTIVE" : "ACTIVE")}
            >
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
              )}
            >
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
