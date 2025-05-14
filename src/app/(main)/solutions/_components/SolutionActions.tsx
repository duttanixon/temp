"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Solution } from "@/types/solution";
import { solutionService } from "@/services/solutionService"; 
import { 
  canDeprecateSolution, 
  canActivateSolution
} from "@/utils/solutions/solutionHelpers";

type SolutionActionsProps = {
  solution: Solution;
};

export default function SolutionActions({ solution }: SolutionActionsProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  // Determine which actions are available based on solution status
  const canDeprecate = canDeprecateSolution(solution.status);
  const canActivate = canActivateSolution(solution.status);

  const executeAction = async (action: string, displayName: string) => {
    setIsLoading(true);

    try {
      await solutionService.executeSolutionAction(solution.solution_id, action);

      toast.success(`${displayName}が完了しました`, {
        description: `ソリューション「${solution.name}」の${displayName}が正常に完了しました。`,
      });

      // Refresh the page to show updated solution status
      router.refresh();
    } catch (error) {
      console.error(`Error during ${action}:`, error);
      toast.error(`${displayName}エラー`, {
        description:
          error instanceof Error
            ? error.message
            : "予期せぬエラーが発生しました",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeprecate = () => executeAction("deprecate", "非推奨化");
  const handleActivate = () => executeAction("activate", "再有効化");

  return (
    <div className="flex items-center space-x-4">
      {canDeprecate && (
        <button
          onClick={handleDeprecate}
          disabled={isLoading}
          className="bg-orange-600 text-white px-4 py-2 rounded-md text-sm hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50"
        >
          非推奨化
        </button>
      )}

      {canActivate && (
        <button
          onClick={handleActivate}
          disabled={isLoading}
          className="bg-green-600 text-white px-4 py-2 rounded-md text-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
        >
          再有効化
        </button>
      )}

      <button
        onClick={() => router.push(`/solutions/${solution.solution_id}/edit`)}
        disabled={isLoading}
        className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md text-sm hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
      >
        編集
      </button>
    </div>
  );
}