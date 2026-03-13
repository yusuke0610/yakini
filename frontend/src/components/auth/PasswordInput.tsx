import { useState } from "react";

import { EyeIcon } from "../icons/EyeIcon";
import { EyeSlashIcon } from "../icons/EyeSlashIcon";
import styles from "./PasswordInput.module.css";

export function PasswordInput({
  value,
  onChange,
  autoComplete,
  minLength,
}: {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  autoComplete: string;
  minLength?: number;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div className={styles.passwordField}>
      <input
        type={visible ? "text" : "password"}
        value={value}
        onChange={onChange}
        required
        autoComplete={autoComplete}
        minLength={minLength}
      />
      <span
        className={styles.passwordToggle}
        onClick={() => setVisible(!visible)}
        role="button"
        aria-label={visible ? "パスワードを隠す" : "パスワードを表示"}
      >
        {visible ? <EyeSlashIcon /> : <EyeIcon />}
      </span>
    </div>
  );
}
