export function generatePassword(length = 11): string {
  const upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
  const lower = "abcdefghijkmnopqrstuvwxyz";
  const digits = "23456789";
  const all = upper + lower + digits;

  const random = (set: string) => set[Math.floor(Math.random() * set.length)];

  const chars = [random(upper), random(lower), random(digits)];
  for (let i = chars.length; i < length; i++) {
    chars.push(random(all));
  }

  return chars.sort(() => Math.random() - 0.5).join("");
}
