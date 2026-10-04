import { forwardRef } from "react";

import { FormError } from "@/components/ui/form-error";
import { Input, type InputProps } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface AuthFormFieldProps extends Omit<InputProps, "id"> {
  id: string;
  label: string;
  error?: string;
}

/**
 * One labeled field, wired for react-hook-form: forwardRef so the ref from
 * register() reaches the Input, aria-invalid for the error ring, and an
 * associated FormError announced via role="alert".
 */
export const AuthFormField = forwardRef<HTMLInputElement, AuthFormFieldProps>(
  function AuthFormField({ label, error, id, ...inputProps }, ref) {
    return (
      <div className="space-y-1.5">
        <Label htmlFor={id}>{label}</Label>
        <Input
          ref={ref}
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          {...inputProps}
        />
        <FormError id={`${id}-error`}>{error}</FormError>
      </div>
    );
  }
);
