import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default function Home() {
  const cookieStore = cookies();
  const hasToken = cookieStore.has("access_token");
  redirect(hasToken ? "/dashboard" : "/login");
}
