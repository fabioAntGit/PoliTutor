import { createBrowserRouter } from "react-router";
import RootLayout from "@/layouts/RootLayout";
import HomePage from "@/pages/home/HomePage";
import SetupPage from "@/pages/setup/SetupPage";
import ChatPage from "@/pages/chat/ChatPage";
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
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
