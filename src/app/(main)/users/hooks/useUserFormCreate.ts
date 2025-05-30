import axios, { AxiosError } from "axios";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { toast } from "sonner";

type UserResponse = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  verify_password: string;
  role: "ADMIN" | "USER" | "CUSTOMER_ADMIN";
  status: "ACTIVE" | "INACTIVE";
  customer_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
};

export const useUserFormCreate = (accessToken: string, initialRole: string) => {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verifyPassword, setVerifyPassword] = useState("");
  const [role, setRole] = useState(initialRole);
  const [status, setStatus] = useState("ACTIVE");
  const [customer, setCustomer] = useState("");

  const router = useRouter();
  const [errorMessage, setErrorMessage] = useState("");

  const handleCreateUser =
    useCallback(async (): Promise<UserResponse | null> => {
      setErrorMessage("");
      try {
        if (password !== verifyPassword) {
          setErrorMessage("パスワードが一致しません");
          return null;
        }
        if (password.length < 10) {
          setErrorMessage("パスワードは10文字以上である必要があります");
          return null;
        }
        const specialPassword = /[!-/:-@\[\\\]-`{-~]/;
        if (!specialPassword.test(password)) {
          setErrorMessage("パスワードには特殊記号を含める必要があります");
          return null;
        }
        if (!/[A-Z]/.test(password)) {
          setErrorMessage("パスワードには大文字を含める必要があります");
          return null;
        }
        if (!/[a-z]/.test(password)) {
          setErrorMessage("パスワードには小文字を含める必要があります");
          return null;
        }
        const userPayload = {
          first_name: firstName,
          last_name: lastName,
          email: email,
          password: password,
          role: role,
          status: status,
          customer_id: customer || null,
        };

        const userUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users`;
        const response = await axios.post(userUrl, userPayload, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
        });
        toast.success("作成完了", {
          description: "新しいユーザーが正常に作成されました。",
        });
        router.push(`/users`);
        return response.data;
      } catch (error) {
        if (error instanceof AxiosError) {
          console.error("Axios エラー:", error.response?.data);
          const detail = error.response?.data?.detail || "";
          console.error("登録エラー詳細:", error.response?.data);
          setErrorMessage(detail);
        }
        return null;
      }
    }, [
      firstName,
      lastName,
      email,
      password,
      verifyPassword,
      role,
      status,
      customer,
      accessToken,
      router,
      setErrorMessage,
    ]);
  const handleCancel = useCallback((): void => {
    router.push("/users");
  }, [router]);

  const handleSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      handleCreateUser();
    },
    [handleCreateUser]
  );

  return {
    firstName,
    lastName,
    email,
    password,
    verifyPassword,
    role,
    status,
    customer,
    errorMessage,
    setFirstName,
    setLastName,
    setEmail,
    setPassword,
    setVerifyPassword,
    setRole,
    setStatus,
    setCustomer,
    setErrorMessage,
    handleCancel,
    handleSubmit,
  };
};
