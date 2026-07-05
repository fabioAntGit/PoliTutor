import * as usersApi from "@/api/users";

export const UserService = {
  listUsers: usersApi.listUsers,
  createUser: usersApi.createUser,
  updateUser: usersApi.updateUser,
  deleteUser: usersApi.deleteUser,
  deleteMyAccount: usersApi.deleteMyAccount,
};
