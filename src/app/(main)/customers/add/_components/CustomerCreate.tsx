import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";

type Props = {
  errorMessage: string;
  completedMessage: string;
  handleCreate: () => void;
  handleCancel: () => void;
};

const buttonVariants = cva("w-35 text-sm font-normal cursor-pointer", {
  variants: {
    variant: {
      default:
        "bg-[#27AE60] text-[#FFFFFF] hover:bg-[#27AE60] active:bg-[#27AE60] focus:bg-[#27AE60]",
      cancel:
        "bg-[#BDC3C7] text-[#7F8C8D] hover:bg-[#BDC3C7] active:bg-[#BDC3C7] focus:bg-[#BDC3C7]",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});
export const CustomerCreate = ({
  errorMessage,
  completedMessage,
  handleCancel,
}: Props) => {
  // 顧客作成可否のメッセージを表示
  const Message = ({
    message,
    type,
  }: {
    message: string;
    type: "success" | "error";
  }) => {
    return (
      <div
        className={cn(
          "text-sm",
          type === "success" ? "text-green-500" : "text-red-500"
        )}
      >
        {message}
      </div>
    );
  };
  return (
    <>
      <div className="flex gap-2">
        <Button
          className={buttonVariants({ variant: "default" })}
          type="submit"
        >
          作成
        </Button>
        <Button
          className={buttonVariants({ variant: "cancel" })}
          type="button"
          onClick={handleCancel}
        >
          キャンセル
        </Button>
      </div>
      {completedMessage && !errorMessage && (
        <Message message={completedMessage} type="success" />
      )}
      {errorMessage && <Message message={errorMessage} type="error" />}
    </>
  );
};
