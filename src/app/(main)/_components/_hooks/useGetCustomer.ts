import { customerService } from "@/services/customerService";
import { Customer } from "@/types/customer";
import { useEffect, useState } from "react";

export const useGetCustomer = () => {
  const [customer, setCustomer] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    customerService
      .getCustomers()
      .then((data) => {
        setCustomer(data ?? []);
        setError(null);
      })
      .catch((error) => {
        setError(error.message ?? "顧客情報の取得に失敗しました");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  return { customer, isLoading, error };
};
