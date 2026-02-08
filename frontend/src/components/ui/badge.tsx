import { classNames } from "@/lib/utils";

type BadgeVariant = "default" | "success" | "danger";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-blue-50 text-primary",
  success: "bg-green-50 text-success",
  danger: "bg-red-50 text-danger",
};

export function Badge({ children, variant = "default" }: BadgeProps) {
  return (
    <span
      className={classNames(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variantClasses[variant],
      )}
    >
      {children}
    </span>
  );
}
