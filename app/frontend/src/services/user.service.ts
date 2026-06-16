import * as usersApi from "@/api/users";

export const UserService = {
  listUsers: usersApi.listUsers,
  getUser: usersApi.getUser,
  createUser: usersApi.createUser,
  updateUser: usersApi.updateUser,
  deleteUser: usersApi.deleteUser,
  deleteMyAccount: usersApi.deleteMyAccount,
};
