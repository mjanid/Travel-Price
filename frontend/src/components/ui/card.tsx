import { classNames } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hover?: boolean;
}

export function Card({ children, className, onClick, hover }: CardProps) {
  return (
    <div
      className={classNames(
        "rounded-lg border border-border bg-card p-6 shadow-sm",
        hover && "cursor-pointer transition-colors hover:bg-card-hover",
        className,
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
