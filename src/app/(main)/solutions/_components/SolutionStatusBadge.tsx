import { SolutionStatus } from '@/types/solution';
import { getStatusColor, getStatusLabel } from '@/utils/solutions/solutionHelpers';

type SolutionStatusBadgeProps = {
  status: SolutionStatus;
  showLabel?: boolean;
  size?: 'sm' | 'md';
};

export default function SolutionStatusBadge({ 
  status, 
  showLabel = true,
  size = 'md' 
}: SolutionStatusBadgeProps) {
  const bgColor = getStatusColor(status);
  const label = getStatusLabel(status);

  // Size classes for the indicator dot
  const dotSize = size === 'sm' ? 'h-2 w-2' : 'h-2.5 w-2.5';
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <span className="inline-flex items-center">
      <span className={`${dotSize} rounded-full ${bgColor} mr-2`}></span>
      {showLabel && (
        <span className={`${textSize} text-[#2C3E50]`}>
          {label}
        </span>
      )}
    </span>
  );
}