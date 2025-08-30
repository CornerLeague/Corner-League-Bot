import { SignIn } from "@clerk/clerk-react";
import { useLocation } from "wouter";
import { useEffect } from "react";
import { useUser } from "@clerk/clerk-react";

export default function SignInPage() {
  const { isSignedIn } = useUser();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (isSignedIn) {
      setLocation("/");
    }
  }, [isSignedIn, setLocation]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome back
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to your sports media account
          </p>
        </div>

        <div className="bg-white py-8 px-6 shadow-xl rounded-lg">
          <SignIn
            appearance={{
              elements: {
                rootBox: "mx-auto",
                card: "shadow-none border-0",
                headerTitle: "hidden",
                headerSubtitle: "hidden",
                socialButtonsBlockButton: "w-full justify-center border border-gray-300 hover:bg-gray-50",
                socialButtonsBlockButtonText: "text-gray-700 font-medium",
                dividerLine: "bg-gray-200",
                dividerText: "text-gray-500 text-sm",
                formFieldInput: "border-gray-300 focus:border-indigo-500 focus:ring-indigo-500",
                formButtonPrimary: "bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md transition-colors",
                footerActionLink: "text-indigo-600 hover:text-indigo-500 font-medium",
                identityPreviewText: "text-gray-700",
                identityPreviewEditButton: "text-indigo-600 hover:text-indigo-500"
              }
            }}
            redirectUrl="/"
          />
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <a
              href="/sign-up"
              className="font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
            >
              Sign up here
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
