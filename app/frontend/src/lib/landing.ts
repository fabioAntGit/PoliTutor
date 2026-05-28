export function landingForRole(role: string | null): string {
  switch (role) {
    case "admin":
      return "/admin";
    case "teacher":
      return "/dashboard";
    case "student":
      return "/";
    default:
      return "/login";
  }
}
