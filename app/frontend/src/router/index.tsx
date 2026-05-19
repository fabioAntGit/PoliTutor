import { createBrowserRouter } from "react-router";

import DashboardLayout from "@/layouts/DashboardLayout";
import RootLayout from "@/layouts/RootLayout";
import HomePage from "@/pages/home/HomePage";
import SetupPage from "@/pages/setup/SetupPage";
import ChatPage from "@/pages/chat/ChatPage";
import DashboardPage from "@/pages/dashboard/DashboardPage";
import CourseDashboardPage from "@/pages/dashboard/CourseDashboardPage";
import NotFoundPage from "@/pages/not-found/NotFoundPage"
import ChatGuard from "@/guards/ChatGuard";
import SessionGuard from "@/guards/SessionGuard";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      {
        path: "setup",
        element: <SetupPage />,
      },
      {
        element: <SessionGuard />,
        children: [
          {
            index: true,
            element: <HomePage />,
          },
          {
            path: "chat/:conversationId",
            element: <ChatGuard />,
            children: [
              {
                index: true,
                element: <ChatPage />,
              },
            ],
          },
        ],
      },
      {
        // TODO: protect with ProfessorGuard once Moodle auth is integrated
        path: "dashboard",
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
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
