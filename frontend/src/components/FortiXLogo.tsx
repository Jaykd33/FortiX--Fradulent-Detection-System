import { Shield } from "lucide-react";

interface FortiXLogoProps {
  className?: string;
}

export const FortiXLogo = ({ className }: FortiXLogoProps) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="bg-primary p-2 rounded-lg">
        <Shield className="h-6 w-6 text-primary-foreground" />
      </div>
      <span className="text-xl font-bold text-foreground">FortiX</span>
    </div>
  );
};