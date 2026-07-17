import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function Home() {
  const cookieStore = await cookies();
  const hasToken = cookieStore.has("access_token");
  redirect(hasToken ? "/dashboard" : "/login");
}
