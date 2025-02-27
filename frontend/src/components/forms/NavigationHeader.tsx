import {useRouter} from "next/navigation";
import {Button} from "@/components/ui/button";
import {ArrowLeft} from "lucide-react";
import React from "react";

export function NavigationHeader() {
  const router = useRouter();

  return (
    <div className="flex justify-between items-center mb-6">
      <Button
        variant="outline"
        onClick={() => router.push('/dashboard')}
        className="flex items-center gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Button>
    </div>
  );
}