import { Outlet } from "react-router-dom";
import { AppNavigation } from "@/components/AppNavigation";

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppNavigation />

      <main className="container mx-auto px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}