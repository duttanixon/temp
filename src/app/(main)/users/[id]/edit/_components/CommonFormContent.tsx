// import { cva } from "class-variance-authority";
// import { FormField } from "@/components/forms/FormField";
// import { FieldErrors, UseFormRegister } from "react-hook-form";
// import { UserEditFormValues } from "@/schemas/userSchemas";

// type Props = {
//   register: UseFormRegister<UserEditFormValues>;
//   errors: FieldErrors;
// };

// export const formVariants = cva("", {
//   variants: {
//     variant: {
//       label: "text-sm font-normal text-[#7F8C8D]",
//       input: "w-155 h-10 border border-[#BDC3C7] rounded-md",
//       inputName: "w-75 h-10 border border-[#BDC3C7] rounded-md",
//       userInfo: "text-lg font-bold text-[#2C3E50]",
//     },
//   },
//   defaultVariants: {
//     variant: "userInfo",
//   },
// });

// export const CommonFormContent = ({ register, errors }: Props) => {
//   return (
//     <>
//       <div className="flex items-center gap-x-16">
//         <h2 className={formVariants({ variant: "userInfo" })}>ユーザー情報</h2>
//         <span className="text-sm font-formal text-[#7F8C8D]">
//           <span className="text-[#FF0000]">*</span>必須項目
//         </span>
//       </div>
//       <div className="flex flex-col items-center gap-2">
//         <div className="flex gap-5">
//           <FormField
//             id="last_name"
//             label="姓"
//             type="text"
//             register={register}
//             errors={errors}
//             required
//             as="input"
//             labelClassName={formVariants({ variant: "label" })}
//             inputClassName={formVariants({ variant: "inputName" })}
//           />
//           <FormField
//             id="first_name"
//             label="名"
//             type="text"
//             register={register}
//             errors={errors}
//             required
//             as="input"
//             labelClassName={formVariants({ variant: "label" })}
//             inputClassName={formVariants({ variant: "inputName" })}
//           />
//         </div>
//         <FormField
//           id="email"
//           label="メールアドレス"
//           type="email"
//           register={register}
//           errors={errors}
//           required
//           as="input"
//           labelClassName={formVariants({ variant: "label" })}
//           inputClassName={formVariants({ variant: "input" })}
//         />
//       </div>
//     </>
//   );
// };
