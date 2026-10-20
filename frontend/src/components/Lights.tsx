export type LightStatus = "ok" | "fail" | "warn" | "idle" | "run";

export type CheckResult = {
  id: string;
  title: string;
  group: string;
  status: LightStatus;
  detail: string;
};

export function Light({ status }: { status: LightStatus }) {
  return <i className={`lamp ${status}`} aria-hidden />;
}

export function LightRow({
  title,
  status,
  detail,
  onRun,
  running,
  dense,
}: {
  title: string;
  status: LightStatus;
  detail?: string;
  onRun?: () => void;
  running?: boolean;
  dense?: boolean;
}) {
  return (
    <div className={`light-row ${status}${dense ? " dense" : ""}`} title={detail}>
      <Light status={running ? "run" : status} />
      <div>
        <b>{title}</b>
        {detail && !dense ? <span>{detail}</span> : null}
      </div>
      {onRun ? (
        <button className="btn btn-quiet btn-sm" type="button" onClick={onRun} disabled={running}>
          Test
        </button>
      ) : null}
    </div>
  );
}
