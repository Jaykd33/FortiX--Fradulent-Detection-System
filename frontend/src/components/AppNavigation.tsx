import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FortiXLogo } from "./FortiXLogo";
import { Link, useLocation } from "react-router-dom";
import { 
  Home, 
  Activity, 
  Shield, 
  Users, 
  Settings, 
  BarChart3, 
  AlertTriangle,
  Menu,
  X,
  BookOpen,
  Brain
} from "lucide-react";

export const AppNavigation = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { label: "Dashboard", icon: Home, path: "/", active: location.pathname === "/" },
    { label: "Analytics", icon: BarChart3, path: "/analytics", active: location.pathname === "/analytics" },
    { label: "Transactions", icon: Activity, path: "/transactions", active: location.pathname === "/transactions" },
    { label: "Alerts", icon: AlertTriangle, path: "/alerts", active: location.pathname === "/alerts" },
    { label: "Upload", icon: Brain, path: "/upload", active: location.pathname === "/upload" },
    { label: "Entities", icon: Users, path: "/entities", active: location.pathname === "/entities" },
    { label: "Guide", icon: BookOpen, path: "/guide", active: location.pathname === "/guide" }
  ];

  return (
    <nav className="bg-card border-b border-border shadow-soft">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <FortiXLogo />
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-3">
            {navItems.map((item) => (
              <Link key={item.label} to={item.path}>
                <Button
                  variant={item.active ? "default" : "ghost"}
                  size="sm"
                  className={`flex items-center gap-2 ${
                    item.active 
                      ? "bg-primary text-primary-foreground" 
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Button>
              </Link>
            ))}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-border">
            <div className="flex flex-col space-y-3">
              {navItems.map((item) => (
                <Link key={item.label} to={item.path} onClick={() => setIsMobileMenuOpen(false)}>
                  <Button
                    variant={item.active ? "default" : "ghost"}
                    size="sm"
                    className={`flex items-center gap-2 justify-start w-full ${
                      item.active 
                        ? "bg-primary text-primary-foreground" 
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </Button>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};