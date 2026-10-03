import QcMetricCard from "./QcMetricCard";
import QualityChart from "./QualityChart";
import QualityDistribution from "./QualityDistribution";
import GcChart from "./GcChart";


type Props = {
  result: any;
};


export default function QcDashboard({
  result,
}: Props) {

  if (!result?.metrics) {
    return null;
  }

  const metrics =
    result.metrics;


  const qualityDistribution = [
    {
      quality: "<20",
      percentage:
        Math.max(
          0,
          100 - metrics.q20_percent
        ),
    },
    {
      quality: "20-29",
      percentage:
        Math.max(
          0,
          metrics.q20_percent -
          metrics.q30_percent
        ),
    },
    {
      quality: "30-39",
      percentage:
        Math.max(
          0,
          metrics.q30_percent -
          metrics.q40_percent
        ),
    },
    {
      quality: "≥40",
      percentage:
        metrics.q40_percent,
    },
  ];


  return (
    <section
      style={{
        marginTop: "40px",
      }}
    >

      {/* HEADER */}

      <div
        style={{
          marginBottom: "24px",
        }}
      >

        <div
          style={{
            fontSize: "12px",
            fontWeight: 700,
            letterSpacing: "0.08em",
            color: "#64748b",
          }}
        >
          SEQUENCING QUALITY CONTROL
        </div>

        <h2
          style={{
            margin: "6px 0",
            fontSize: "28px",
            color: "#0f172a",
          }}
        >
          FastQC Analysis
        </h2>

        <p
          style={{
            color: "#64748b",
          }}
        >
          Quality assessment of the uploaded sequencing reads.
        </p>

      </div>


      {/* METRICS */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >

        <QcMetricCard
          label="READS"
          value={metrics.read_count}
        />

        <QcMetricCard
          label="MEAN QUALITY"
          value={`Q${metrics.mean_quality}`}
          status={
            metrics.mean_quality >= 30
              ? "pass"
              : "warning"
          }
        />

        <QcMetricCard
          label="Q20"
          value={`${metrics.q20_percent}%`}
          status={
            metrics.q20_percent >= 90
              ? "pass"
              : "warning"
          }
        />

        <QcMetricCard
          label="Q30"
          value={`${metrics.q30_percent}%`}
          status={
            metrics.q30_percent >= 90
              ? "pass"
              : "warning"
          }
        />

        <QcMetricCard
          label="Q40"
          value={`${metrics.q40_percent}%`}
        />

        <QcMetricCard
          label="MEAN READ LENGTH"
          value={metrics.mean_read_length}
          unit="bp"
        />

      </div>


      {/* QUALITY CHART */}

      <div
        style={{
          marginBottom: "24px",
        }}
      >

        <QualityChart
          data={metrics.per_cycle_quality}
        />

      </div>


      {/* SECOND ROW */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(350px, 1fr))",
          gap: "24px",
        }}
      >

        <QualityDistribution
          data={qualityDistribution}
        />

        <GcChart
          gcPercentage={
            metrics.mean_gc_percent
          }
        />

      </div>

    </section>
  );
}
