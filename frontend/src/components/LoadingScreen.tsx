import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

const loadingSteps = [
  'Finding relevant papers…',
  'Reading newsletters…',
  'Synthesizing insights…',
  'Preparing your podcast…'
];

export function LoadingScreen() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < loadingSteps.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-16">
      <div className="w-full max-w-[720px] mx-auto">
        <div className="bg-white rounded-2xl shadow-sm border border-neutral-200 p-12">
          {/* Spinner */}
          <div className="flex justify-center mb-8">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
          </div>

          {/* Loading Steps */}
          <div className="space-y-4">
            {loadingSteps.map((step, index) => (
              <div
                key={index}
                className={`text-center text-lg transition-all duration-500 ${
                  index === currentStep
                    ? 'text-neutral-900 font-medium scale-105'
                    : index < currentStep
                    ? 'text-neutral-400'
                    : 'text-neutral-300'
                }`}
              >
                {step}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
