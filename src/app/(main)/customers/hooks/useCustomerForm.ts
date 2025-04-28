import { useState } from "react";

export const useCustomerFormBasic = () => {
  const [activeTab, setActiveTab] = useState("basic");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [completedMessage, setCompletedMessage] = useState("");

  return {
    activeTab,
    setActiveTab,
    companyName,
    setCompanyName,
    email,
    setEmail,
    address,
    setAddress,
    errorMessage,
    setErrorMessage,
    completedMessage,
    setCompletedMessage,
  };
};
