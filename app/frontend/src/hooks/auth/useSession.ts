import { useNavigate } from "react-router";
import { AuthService } from "@/services/auth.service";

export function useSession() {
  const navigate = useNavigate();

  const logout = async () => {
    const accessToken = AuthService.getAccessToken();
    if (accessToken) {
      await AuthService.logout().catch(() => {});
    }
    AuthService.clearTokens();
    navigate("/login", { replace: true });
  };

  return {
    fullName: AuthService.getFullName(),
    username: AuthService.getUsername(),
    role: AuthService.getRole(),
    logout,
  };
}
