import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const tabVariants = cva(
  "relative flex w-[115px] h-[44.4px] text-center items-center justify-center text-sm font-normal cursor-pointer",
  {
    variants: {
      active: {
        true: "bg-[#3498DB] text-[#FFFFFF]",
        false: "bg-[#FFFFFF] text-[#7F8C8D]",
      },
    },
  }
);

type Props = {
  activeTab: string;
  onChange: (tab: string) => void;
};
const tabs = [
  { id: "basic", label: "基本情報" },
  { id: "subscription", label: "サブスクリプション" },
];

export const TabsNav = ({ activeTab, onChange }: Props) => {
  return (
    <div className="inline-flex shadow-none">
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            tabVariants({ active: activeTab === tab.id }),
            index !== tabs.length - 1 && "border-r border-[#BDC3C7]"
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};
