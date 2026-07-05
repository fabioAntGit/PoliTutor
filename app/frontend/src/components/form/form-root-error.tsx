interface FormRootErrorProps {
  message?: string;
}

export function FormRootError({ message }: FormRootErrorProps) {
  if (!message) return null;
  return (
    <p className="text-sm text-destructive p-2 bg-destructive/10 rounded-md text-center">
      {message}
    </p>
  );
}
