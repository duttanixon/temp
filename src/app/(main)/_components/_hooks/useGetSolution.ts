import { solutionService } from "@/services/solutionService";
import { Solution } from "@/types/solution";
import { useEffect, useState } from "react";

export const useGetSolution = () => {
  const [solution, setSolution] = useState<Solution[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    solutionService
      .getSolutions()
      .then((data) => {
        setSolution(data ?? []);
        setError(null);
      })
      .catch((error) => {
        setError(error.message ?? "ソリューション情報の取得に失敗しました");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  return { solution, isLoading, error };
};
