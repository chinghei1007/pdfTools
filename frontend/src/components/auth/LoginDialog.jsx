import { useState } from "react";
import { Dialog } from "@components/dialogs/Dialog";
import { Input } from "@components/inputs/Fields";
import { Button } from "@components/buttons/Button";

function LoginForm({ onSubmit, loading, error, onRegister, onForgotPassword }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (!loading && onSubmit)
          onSubmit({ username: username.trim(), password });
      }}
    >
      <Input
        label="Username or email"
        name="username"
        autoComplete="username"
        required
        value={username}
        onChange={(event) => setUsername(event.target.value)}
        disabled={loading}
      />
      <Input
        label="Password"
        name="password"
        type="password"
        autoComplete="current-password"
        required
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        disabled={loading}
      />
      {error && (
        <p role="alert" className="m-0 text-sm text-red-700">
          {error}
        </p>
      )}
      <Button
        type="submit"
        loading={loading}
        disabled={!onSubmit || !username.trim() || !password}
      >
        Log in
      </Button>
      <div className="flex flex-wrap justify-between gap-2">
        {onForgotPassword && (
          <Button variant="ghost" onClick={onForgotPassword}>
            Forgot password?
          </Button>
        )}
        {onRegister && (
          <Button variant="ghost" onClick={onRegister}>
            Create account
          </Button>
        )}
      </div>
    </form>
  );
}

export function LoginDialog({ open, onClose, ...props }) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Log in"
      description="Access your account and document history."
    >
      <LoginForm {...props} />
    </Dialog>
  );
}
