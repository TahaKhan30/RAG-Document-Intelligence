import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import LogoutButton from "@/components/LogoutButton";

async function getCurrentUser() {
  const cookieStore = cookies();
  const token = cookieStore.get("access_token");
  if (!token) redirect("/login");

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/me`, {
    headers: { Cookie: `access_token=${token.value}` },
    cache: "no-store",
  });

  if (!res.ok) redirect("/login");
  return res.json();
}

export default async function DashboardPage() {
  const user = await getCurrentUser();

  return (
    <main className="min-h-screen bg-gray-50 p-10">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          <LogoutButton />
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <p className="text-sm text-gray-500 mb-1">Signed in as</p>
          <p className="text-lg font-medium text-gray-900">{user.email}</p>
          {user.full_name && (
            <p className="text-sm text-gray-500 mt-0.5">{user.full_name}</p>
          )}
          <div className="mt-6 pt-6 border-t border-gray-100">
            <p className="text-xs text-gray-400">
              This page is server-rendered. The user was fetched from FastAPI using the
              HttpOnly cookie — JavaScript on this page has no access to the token.
            </p>
          </div>
        </div>

        {/* When you add features, drop protected API calls here using the same cookie pattern */}
      </div>
    </main>
  );
}
