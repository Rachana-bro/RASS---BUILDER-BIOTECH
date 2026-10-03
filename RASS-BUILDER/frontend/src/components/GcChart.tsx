import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";


type Props = {
  gcPercentage: number;
};


export default function GcChart({
  gcPercentage,
}: Props) {

  const data = [
    {
      name: "Sample",
      gc: gcPercentage,
    },
  ];

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

      <h3
        style={{
          marginTop: 0,
          color: "#0f172a",
        }}
      >
        GC Content
      </h3>

      <p
        style={{
          color: "#64748b",
          fontSize: "13px",
        }}
      >
        Average percentage of guanine and cytosine bases
      </p>


      <div style={{ height: 250, minHeight: 250, width: "100%" }}>

        <ResponsiveContainer width="100%" height="100%">

          <BarChart
            data={data}
            layout="vertical"
          >

            <XAxis
              type="number"
              domain={[0, 100]}
            />

            <YAxis
              type="category"
              dataKey="name"
            />

            <Tooltip />

            <Bar
              dataKey="gc"
              fill="#334155"
              radius={[0, 4, 4, 0]}
            />

          </BarChart>

        </ResponsiveContainer>

      </div>


      <div
        style={{
          textAlign: "center",
          fontSize: "28px",
          fontWeight: 700,
          color: "#0f172a",
        }}
      >
        {gcPercentage}%
      </div>

    </div>
  );
}
