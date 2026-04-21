import { createBrowserRouter } from "react-router";
import RootLayout from "@/layouts/RootLayout";
import HomePage from "@/pages/home/HomePage";
import SetupPage from "@/pages/setup/SetupPage";
import ChatPage from "@/pages/chat/ChatPage";
import NotFoundPage from "@/pages/not-found/NotFoundPage"
import ChatGuard from "@/guards/ChatGuard";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "setup/:projectId",
        element: <SetupPage />,
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
      {
        path: "*",
        element: <NotFoundPage />,
      },
      
    ],
  },
]);
