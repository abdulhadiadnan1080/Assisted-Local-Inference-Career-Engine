import { useState } from "react";
import type { ReactNode } from "react";

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <span className="hint">{hint}</span> : null}
    </label>
  );
}

export function Toggle({
  title,
  note,
  on,
  onChange,
  locked,
}: {
  title: string;
  note?: string;
  on: boolean;
  onChange: (next: boolean) => void;
  locked?: boolean;
}) {
  return (
    <div className="toggle">
      <div>
        <p>{title}</p>
        {note ? <span>{note}</span> : null}
      </div>
      <button
        type="button"
        aria-pressed={on}
        aria-label={title}
        className={`switch${on ? " on" : ""}${locked ? " locked" : ""}`}
        onClick={() => !locked && onChange(!on)}
      >
        <i />
      </button>
    </div>
  );
}

export function TagInput({
  values,
  onChange,
  placeholder,
}: {
  values: string[];
  onChange: (next: string[]) => void;
  placeholder: string;
}) {
  const [text, setText] = useState("");

  function commit() {
    const value = text.trim().replace(/,$/, "");
    if (value && !values.includes(value)) onChange([...values, value]);
    setText("");
  }

  return (
    <div className="tags">
      {values.map((v) => (
        <span className="tagitem" key={v}>
          {v}
          <button type="button" onClick={() => onChange(values.filter((x) => x !== v))} aria-label={`Remove ${v}`}>
            ×
          </button>
        </span>
      ))}
      <input
        value={text}
        placeholder={placeholder}
        onChange={(e) => setText(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            commit();
          }
          if (e.key === "Backspace" && !text && values.length) onChange(values.slice(0, -1));
        }}
      />
    </div>
  );
}

export function Toast({ message }: { message: string }) {
  return <div className="toast">{message}</div>;
}

export function Banner({
  tone = "info",
  children,
}: {
  tone?: "info" | "warn";
  children: ReactNode;
}) {
  return <div className={`banner ${tone}`}>{children}</div>;
}
