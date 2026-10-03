type Props = {
  label: string;
  value: string | number;
  unit?: string;
  status?: "pass" | "warning" | "fail";
};


export default function QcMetricCard({
  label,
  value,
  unit,
  status = "pass",
}: Props) {

  const statusText = {
    pass: "PASS",
    warning: "CHECK",
    fail: "FAIL",
  };

  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "20px",
      }}
    >

      <div
        style={{
          fontSize: "13px",
          color: "#64748b",
          marginBottom: "10px",
        }}
      >
        {label}
      </div>

      <div
        style={{
          fontSize: "28px",
          fontWeight: 700,
          color: "#0f172a",
        }}
      >
        {value}
        {unit && (
          <span
            style={{
              fontSize: "14px",
              marginLeft: "4px",
              color: "#64748b",
            }}
          >
            {unit}
          </span>
        )}
      </div>

      <div
        style={{
          marginTop: "10px",
          fontSize: "11px",
          fontWeight: 700,
          letterSpacing: "0.06em",
          color:
            status === "pass"
              ? "#15803d"
              : status === "warning"
                ? "#a16207"
                : "#b91c1c",
        }}
      >
        {statusText[status]}
      </div>

    </div>
  );
}
