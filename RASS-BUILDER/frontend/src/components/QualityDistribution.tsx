import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";


type Props = {
  data: {
    quality: string;
    percentage: number;
  }[];
};


export default function QualityDistribution({
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

      <h3
        style={{
          marginTop: 0,
          color: "#0f172a",
        }}
      >
        Quality Distribution
      </h3>

      <p
        style={{
          color: "#64748b",
          fontSize: "13px",
        }}
      >
        Distribution of bases by Phred quality range
      </p>


      <div
        style={{
          width: "100%",
          height: 300,
          minHeight: 300,
        }}
      >

        <ResponsiveContainer width="100%" height="100%">

          <BarChart data={data}>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
            />

            <XAxis dataKey="quality" />

            <YAxis
              label={{
                value: "%",
                angle: -90,
                position: "insideLeft",
              }}
            />

            <Tooltip />

            <Bar
              dataKey="percentage"
              fill="#475569"
              radius={[4, 4, 0, 0]}
            />

          </BarChart>

        </ResponsiveContainer>

      </div>

    </div>
  );
}
