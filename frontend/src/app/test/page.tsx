// src/app/test/page.tsx
'use client';

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useState } from "react"

export default function TestComponents() {
  const [inputValue, setInputValue] = useState("")

  return (
    <div className="p-8 space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Component Test Page</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Test Button variants */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Buttons</h3>
            <div className="flex gap-2">
              <Button>Default Button</Button>
              <Button variant="destructive">Destructive</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="secondary">Secondary</Button>
            </div>
          </div>

          {/* Test Input and Label */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Input with Label</h3>
            <div className="grid w-full max-w-sm items-center gap-1.5">
              <Label htmlFor="test-input">Test Input</Label>
              <Input
                type="text"
                id="test-input"
                placeholder="Type something..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
              />
            </div>
          </div>

          {/* Test Alert */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Alerts</h3>
            <Alert>
              <AlertDescription>This is a default alert</AlertDescription>
            </Alert>
            <Alert variant="destructive">
              <AlertDescription>This is a destructive alert</AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}