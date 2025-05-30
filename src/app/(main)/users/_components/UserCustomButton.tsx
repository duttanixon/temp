import { Button } from "@/components/ui/button";
import { cva } from "class-variance-authority";

type Props = {
  handleCancel: () => void;
  mainUnit?: string;
  subUnit?: string;
};

const buttonVariants = cva("w-35 text-sm font-normal cursor-pointer", {
  variants: {
    variant: {
      default:
        "bg-[#27AE60] text-[#FFFFFF] hover:bg-[#219653] active:bg-[#27AE60] focus:bg-[#219653]",
      cancel:
        "bg-[#BDC3C7] text-[#7F8C8D] hover:bg-[#A6ACAF] active:bg-[#BDC3C7] focus:bg-[#A6ACAF]",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export const UserCustomButton = ({
  handleCancel,
  mainUnit,
  subUnit,
}: Props) => {
  return (
    <>
      <div className="flex gap-2">
        <Button
          className={buttonVariants({ variant: "default" })}
          type="submit"
        >
          {mainUnit}
        </Button>
        <Button
          className={buttonVariants({ variant: "cancel" })}
          type="button"
          onClick={handleCancel}
        >
          {subUnit}
        </Button>
      </div>
    </>
  );
};
