import { SignUp } from "@clerk/clerk-react";
import { useLocation } from "wouter";
import { useEffect } from "react";
import { useUser } from "@clerk/clerk-react";

export default function SignUpPage() {
  const { isSignedIn } = useUser();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (isSignedIn) {
      setLocation("/questionnaire");
    }
  }, [isSignedIn, setLocation]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Join the ultimate sports media platform
          </p>
        </div>
        
        <div className="bg-white py-8 px-6 shadow-xl rounded-lg">
          <SignUp 
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
                formFieldInput: "border-gray-300 focus:border-emerald-500 focus:ring-emerald-500",
                formButtonPrimary: "bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-md transition-colors",
                footerActionLink: "text-emerald-600 hover:text-emerald-500 font-medium",
                identityPreviewText: "text-gray-700",
                identityPreviewEditButton: "text-emerald-600 hover:text-emerald-500"
              }
            }}
            redirectUrl="/questionnaire"
          />
        </div>
        
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <a 
              href="/sign-in" 
              className="font-medium text-emerald-600 hover:text-emerald-500 transition-colors"
            >
              Sign in here
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}