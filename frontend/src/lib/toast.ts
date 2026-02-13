import { toast as sonnerToast } from "sonner";

export const toast = {
  success: (message: string) => sonnerToast.success(message, { duration: 4000 }),
  error: (message: string) => sonnerToast.error(message, { duration: 5000 }),
  info: (message: string) => sonnerToast(message, { duration: 3000 }),
  loading: (message: string) => sonnerToast.loading(message),
  dismiss: (id?: string | number) => sonnerToast.dismiss(id),
  promise: <T,>(
    promise: Promise<T>,
    messages: { loading: string; success: string; error: string },
  ) => sonnerToast.promise(promise, messages),
};
