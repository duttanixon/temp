import { type FC } from "react";

import {
  type NameType,
  type ValueType,
} from "recharts/types/component/DefaultTooltipContent";

import { cn } from "@/lib/utils";

type CustomTooltipContentProps = {
  label?: string;
  seriesName: NameType;
  value: ValueType;
  unit?: string;
  indicatorClass?: string;
  total?: number | undefined;
};

export const CustomTooltipContent: FC<CustomTooltipContentProps> = ({
  label,
  seriesName,
  value,
  unit,
  indicatorClass,
  total,
}) => {
  return (
    <div className="flex flex-col gap-1 w-full max-w-40">
      {label != null && <div className="text-foreground truncate">{label}</div>}
      <div className="flex justify-between gap-1 w-full">
        <div className="flex items-center gap-1 min-w-0 flex-1">
          <div className={cn("size-2 shrink-0 rounded-xs", indicatorClass)} />
          <span className="text-foreground-alt truncate">{seriesName}</span>
        </div>
        <div className="flex">
          <span className="text-foreground">{value}</span>
          <span className="text-foreground-alt">{unit}</span>
        </div>
      </div>
      {total != null && (
        <div className="mt-1.5 flex basis-full items-center border-t pt-1.5 text-xs text-foreground">
          Total
          <div className="ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums text-foreground">
            {total}
            <span className="font-normal text-muted-foreground">{unit}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomTooltipContent;
