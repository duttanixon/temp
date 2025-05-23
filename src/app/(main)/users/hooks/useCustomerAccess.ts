import axios from "axios";
import { useEffect, useState } from "react";

type CustomerResponse = {
  name: string;
  contact_email: string;
  address: string;
  status: string;
  customer_id: string;
};

const fetchCustomers = async (
  accessToken: string
): Promise<CustomerResponse[]> => {
  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers`;

  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/json",
    },
  });
  return response.data as CustomerResponse[];
};

export const useCustomerAccess = (accessToken: string) => {
  const [customers, setCustomers] = useState<CustomerResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const loadCustomers = async () => {
      try {
        setLoading(true);
        const data = await fetchCustomers(accessToken);
        setCustomers(data);
        setError(null);
      } catch (error) {
        console.error("Error fetching customers:", error);
        setError("顧客情報の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      loadCustomers();
    }
  }, [accessToken]);
  return { customers, loading, error };
};
