export const resetFormAfterDelay = (
  options: {
    clearName?: boolean;
    clearEmail?: boolean;
    clearAddress?: boolean;
    clearCompletedMessage?: boolean;
    clearErrorMessage?: boolean;
  },
  setters: {
    setCompanyName: (val: string) => void;
    setEmail: (val: string) => void;
    setAddress: (val: string) => void;
    setCompletedMessage: (val: string) => void;
    setErrorMessage: (val: string) => void;
  }
) => {
  const {
    clearName = false,
    clearEmail = false,
    clearAddress = false,
    clearCompletedMessage = false,
    clearErrorMessage = false,
  } = options;
  const {
    setCompanyName,
    setEmail,
    setAddress,
    setCompletedMessage,
    setErrorMessage,
  } = setters;

  if (clearName) setCompanyName("");
  if (clearEmail) setEmail("");
  if (clearAddress) setAddress("");
  setTimeout(() => {
    if (clearCompletedMessage) setCompletedMessage("");
    if (clearErrorMessage) setErrorMessage("");
  }, 5000);
};
