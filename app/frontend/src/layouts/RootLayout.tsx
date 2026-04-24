import { Outlet } from "react-router";
import { Toaster } from "sonner";

export default function RootLayout() {
  return (
    <>
      <Outlet />
      <Toaster richColors position="bottom-right" />
    </>
  );
}
