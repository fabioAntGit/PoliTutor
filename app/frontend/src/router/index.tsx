import { createBrowserRouter } from "react-router";

import DashboardLayout from "@/layouts/DashboardLayout";
import RootLayout from "@/layouts/RootLayout";
import HomePage from "@/pages/home/HomePage";
import LoginPage from "@/pages/login/LoginPage";
import ChatPage from "@/pages/chat/ChatPage";
import MemoriesPage from "@/pages/memories/MemoriesPage";
import DashboardPage from "@/pages/dashboard/DashboardPage";
import CourseDashboardPage from "@/pages/dashboard/CourseDashboardPage";
import AdminDashboardPage from "@/pages/admin/AdminDashboardPage";
import ChangePasswordPage from "@/pages/change-password/ChangePasswordPage";
import NotFoundPage from "@/pages/not-found/NotFoundPage";
import AuthGuard from "@/guards/AuthGuard";
import RoleGuard from "@/guards/RoleGuard";
import PasswordGuard from "@/guards/PasswordGuard";
import GuestGuard from "@/guards/GuestGuard";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      {
        element: <GuestGuard />,
        children: [
          {
            path: "login",
            element: <LoginPage />,
          },
        ],
      },
      {
        element: <AuthGuard />,
        children: [
          {
            path: "change-password",
            element: <ChangePasswordPage />,
          },
          {
            element: <PasswordGuard />,
            children: [
              {
                element: <RoleGuard roles={["student"]} />,
                children: [
                  {
                    index: true,
                    element: <HomePage />,
                  },
                  {
                    path: "chat/:conversationId",
                    element: <ChatPage />,
                  },
                  {
                    path: "memories",
                    element: <MemoriesPage />,
                  },
                ],
              },
              {
                path: "admin",
                element: <RoleGuard roles={["admin"]} />,
                children: [
                  {
                    index: true,
                    element: <AdminDashboardPage />,
                  },
                ],
              },
              {
                path: "dashboard",
                element: <RoleGuard roles={["teacher", "admin"]} />,
                children: [
                  {
                    element: <DashboardLayout />,
                    children: [
                      {
                        index: true,
                        element: <DashboardPage />,
                      },
                      {
                        path: "courses/:courseId",
                        element: <CourseDashboardPage />,
                      },
                    ],
                  },
                ],
              },
            ],
          },
        ],
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
