import { LoginForm } from '@/components/auth/LoginForm'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Welcome to CampaignMind
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Sign in to enhance your marketing campaign briefs with AI
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}
