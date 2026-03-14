import { SignupForm } from '@/components/auth/SignupForm'
import Link from 'next/link'
import { isGuestModeEnabled } from '@/lib/supabase/config'

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Start enhancing your marketing campaigns with AI
          </p>
        </div>
        <SignupForm />
        {isGuestModeEnabled && (
          <div className="border-t border-gray-200 pt-4">
            <Link
              href="/"
              className="block text-center text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              Continue as guest
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
