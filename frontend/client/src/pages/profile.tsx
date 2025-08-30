/**
 * Profile Page
 *
 * A protected page that displays user profile information and preferences.
 * This page demonstrates the use of ProtectedRoute for authentication guards.
 */

import { ProtectedRoute, UserProfile } from "@/components/auth";

export default function Profile() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center">
                <a
                  href="/"
                  className="text-xl font-black text-black tracking-tight hover:text-gray-700 transition-colors"
                >
                  MLB
                </a>
              </div>
              <nav className="flex items-center space-x-4">
                <a
                  href="/"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Home
                </a>
                <a
                  href="/profile"
                  className="bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Profile
                </a>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="py-8">
          <UserProfile />
        </main>
      </div>
    </ProtectedRoute>
  );
}
