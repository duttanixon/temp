import { type FC } from "react";

import { cn } from "@/lib/utils";

type CustomChartLegendProps = {
  seriesStyles: {
    name: string;
    cssVarColor: string;
    opacity: number;
    opacityClass?: string;
  }[];
};

export const CustomChartLegend: FC<CustomChartLegendProps> = ({
  seriesStyles,
}) => {
  return (
    <div
      data-testid="customChartLegend"
      className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 px-4 my-2" // flex-wrap と gap-y-2 を追加、gap-4 を gap-x-4 に変更
    >
      {seriesStyles.map((style) => (
        <div key={style.name} className="flex items-center gap-1.5 max-w-1/2">
          <div
            className={cn("size-2 shrink-0 rounded-xs", style.opacityClass)}
            style={{ backgroundColor: style.cssVarColor }}
          />
          <div className="text-xs truncate">{style.name}</div>
        </div>
      ))}
    </div>
  );
};

export default CustomChartLegend;
