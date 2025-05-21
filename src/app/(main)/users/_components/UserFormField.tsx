import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type FormFieldProps<
  T extends HTMLInputElement | HTMLSelectElement = HTMLInputElement,
> = {
  id: string;
  label: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<T>) => void;
  required?: boolean;
  labelClassName?: string;
  inputClassName?: string;
  as?: "input" | "toggle";
  options?: { label: string; value: string }[];
  type?: string;
};

export const UserFormField = <
  T extends HTMLInputElement | HTMLSelectElement = HTMLInputElement,
>({
  id,
  label,
  name,
  value,
  onChange,
  required = false,
  labelClassName = "",
  inputClassName = "",
  as = "input",
  type = "text",
}: FormFieldProps<T>) => (
  <div className="flex flex-col gap-1">
    <Label htmlFor={id} className={cn(labelClassName)}>
      {label} {required && <span className="text-[#FF0000]">*</span>}
    </Label>
    {as === "input" && (
      <Input
        className={cn(inputClassName)}
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
