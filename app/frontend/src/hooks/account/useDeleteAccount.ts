import { useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { UserService } from "@/services/user.service";
import { AuthService } from "@/services/auth.service";
import { ApiError } from "@/lib/errors";

export function useDeleteAccount() {
  const navigate = useNavigate();
  const [deleting, setDeleting] = useState(false);

  const deleteAccount = async () => {
    setDeleting(true);
    try {
      await UserService.deleteMyAccount();
      AuthService.clearTokens();
      toast.success("Conta eliminada. Os teus dados serao apagados permanentemente daqui a 30 dias.");
      navigate("/login", { replace: true });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Erro ao eliminar conta.";
      toast.error(message);
      setDeleting(false);
    }
  };

  return { deleting, deleteAccount };
}
