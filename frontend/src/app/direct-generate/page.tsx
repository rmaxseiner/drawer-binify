'use client';

import { GenerateForm } from '@/components/forms/GenerateForm';
import {NavigationHeader} from "@/components/forms/NavigationHeader";
import { ModelsList} from "@/components/forms/ModelsList";


export default function DirectGeneratePage() {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <NavigationHeader />
      <GenerateForm />
      <ModelsList />
    </div>
  );
}