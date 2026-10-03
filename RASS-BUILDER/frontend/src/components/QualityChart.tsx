import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";


type Props = {
  data: {
    cycle: number;
    mean_quality: number;
  }[];
};


export default function QualityChart({
  data,
}: Props) {

  return (
    <div
      style={{
        background: "#ffffff",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        padding: "24px",
        minWidth: 0,
      }}
    >

      <div style={{ marginBottom: "20px" }}>

        <h3
          style={{
            margin: 0,
            color: "#0f172a",
          }}
        >
          Per-Base Sequence Quality
        </h3>

        <p
          style={{
            marginTop: "6px",
            color: "#64748b",
            fontSize: "13px",
          }}
        >
          Mean Phred quality by sequencing cycle
        </p>

      </div>


      <div style={{ width: "100%", height: 350, minHeight: 350 }}>

        <ResponsiveContainer width="100%" height="100%">

          <LineChart data={data}>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
            />

            <XAxis
              dataKey="cycle"
              label={{
                value: "Cycle",
                position: "insideBottom",
                offset: -5,
              }}
            />

            <YAxis
              domain={[0, 45]}
              label={{
                value: "Phred Quality",
                angle: -90,
                position: "insideLeft",
              }}
            />

            <Tooltip />

            <ReferenceLine
              y={30}
              stroke="#64748b"
              strokeDasharray="5 5"
              label="Q30"
            />

            <Line
              type="monotone"
              dataKey="mean_quality"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              name="Mean Q"
            />

          </LineChart>

        </ResponsiveContainer>

      </div>

    </div>
  );
}
