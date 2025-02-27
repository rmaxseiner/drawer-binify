import * as React from "react"
import { cn } from "@/lib/utils"
import {LabelProps} from "@radix-ui/react-label";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {

  customProp?: string;
}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        className
      )}
      {...props}
    />
  )
)
Label.displayName = "Label"

export { Label }