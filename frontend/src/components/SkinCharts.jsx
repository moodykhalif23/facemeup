import ReactECharts from 'echarts-for-react';

const SKIN_PALETTE = {
  Oily:        '#F97316',   // amber-500
  Dry:         '#0EA5E9',   // sky-500
  Combination: '#EAB308',   // yellow-500
  Normal:      '#10B981',   // emerald-500
  Sensitive:   '#A855F7',   // purple-500
};

const COND_PALETTE = {
  Acne:              '#EF4444',   // red-500
  Hyperpigmentation: '#8B5CF6',   // violet-500
  'Uneven tone':     '#F59E0B',   // amber-400
  Dehydration:       '#3B82F6',   // blue-500
  'None detected':   '#10B981',   // emerald-500
};

// Shared ECharts base theme
const baseTextStyle = { color: 'var(--muted-foreground)', fontFamily: 'inherit', fontSize: 12 };


function makeSkinTypeBarOption({ skinData, detectedType }) {
  const labels  = skinData.map((d) => d.name);
  const values  = skinData.map((d) => Math.round(d.value * 100));
  const colors  = skinData.map((d) => ({
    value: Math.round(d.value * 100),
    itemStyle: {
      color:   SKIN_PALETTE[d.name] || '#F97316',
      opacity: d.name === detectedType ? 1 : 0.5,
      borderRadius: [4, 4, 0, 0],
    },
  }));

  return {
    backgroundColor: 'transparent',
    title: {
      text:    'Skin Type Confidence',
      subtext: `Detected: ${detectedType}`,
      textStyle:    { color: 'var(--card-foreground)', fontSize: 14, fontWeight: 700 },
      subtextStyle: { color: 'var(--primary)', fontSize: 12 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'var(--popover)',
      borderColor:     'var(--border)',
      textStyle:       { color: 'var(--popover-foreground)', fontSize: 12 },
      formatter: (params) => `${params[0].name}: <b>${params[0].value}%</b>`,
    },
    legend: { show: false },
    toolbox: { show: false },
    calculable: true,
    grid: { left: 16, right: 24, top: 56, bottom: 8, containLabel: true },
    xAxis: [
      {
        type:  'category',
        data:  labels,
        axisLabel: baseTextStyle,
        axisLine: { lineStyle: { color: 'var(--border)' } },
        axisTick: { show: false },
      },
    ],
    yAxis: [
      {
        type: 'value',
        min:  0,
        max:  100,
        axisLabel: { ...baseTextStyle, formatter: '{value}%' },
        splitLine: { lineStyle: { color: 'var(--border)', type: 'dashed' } },
        axisLine:  { show: false },
        axisTick:  { show: false },
      },
    ],
    series: [
      {
        name: 'Confidence %',
        type: 'bar',
        data: colors,
        barMaxWidth: 48,
        label: {
          show:      true,
          position:  'top',
          formatter: ({ value }) => `${value}%`,
          color:     'var(--muted-foreground)',
          fontSize:  11,
        },
        markPoint: {
          data: [
            { type: 'max', name: 'Max', label: { color: '#fff', fontSize: 11 } },
            { type: 'min', name: 'Min', label: { color: '#fff', fontSize: 11 } },
          ],
          symbolSize: 52,
          itemStyle: { opacity: 0.85 },
        },
        markLine: { data: [] },
        emphasis: { focus: 'self' },
      },
    ],
  };
}

// Nightingale rose pie — condition scores
function makeNightingaleOption({ condData, selectedKeys }) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'var(--popover)',
      borderColor:     'var(--border)',
      textStyle:       { color: 'var(--popover-foreground)', fontSize: 12 },
      formatter: ({ name, value, percent }) =>
        `${name}<br/><b>${Math.round(value * 100)}%</b> (${percent}%)`,
    },
    legend: {
      top:       'bottom',
      textStyle: { color: 'var(--muted-foreground)', fontSize: 11 },
      icon:      'circle',
    },
    toolbox: { show: false },
    series: [
      {
        name:      'Condition Score',
        type:      'pie',
        radius:    ['20%', '72%'],
        center:    ['50%', '46%'],
        roseType:  'area',
        itemStyle: { borderRadius: 8, borderColor: 'var(--card)', borderWidth: 2 },
        label: {
          color:    'var(--muted-foreground)',
          fontSize: 11,
          formatter: ({ name, value }) => `${name}\n${Math.round(value * 100)}%`,
        },
        labelLine: { show: false },
        emphasis: {
          label:     { fontSize: 13, fontWeight: 700 },
          itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,0.4)' },
        },
        data: condData.map((d) => ({
          value: d.value,
          name:  d.name,
          itemStyle: {
            color:   COND_PALETTE[d.name] || 'var(--primary)',
            opacity: selectedKeys.includes(d.name) ? 1 : 0.55,
          },
        })),
      },
    ],
  };
}

// Radar option
function makeRadarOption({ condData, selectedKeys }) {
  const indicators = condData.map(({ name }) => ({
    name,
    max: 1,
    nameTextStyle: { ...baseTextStyle, fontSize: 11 },
  }));

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'var(--popover)',
      borderColor: 'var(--border)',
      textStyle: { color: 'var(--popover-foreground)', fontSize: 12 },
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: 'var(--muted-foreground)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'var(--border)', opacity: 0.5 } },
      splitArea: { show: false },
      axisLine:  { lineStyle: { color: 'var(--border)' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: condData.map((d) => d.value),
            name: 'Condition Score',
            symbol: 'circle',
            symbolSize: 5,
            lineStyle: { color: 'var(--primary)', width: 2 },
            areaStyle: { color: 'var(--primary)', opacity: 0.18 },
            itemStyle: {
              color: (params) =>
                selectedKeys.includes(condData[params.dataIndex]?.name)
                  ? 'var(--primary)'
                  : 'var(--muted-foreground)',
            },
          },
        ],
      },
    ],
  };
}

// Face quality gauge
function makeGaugeOption(score) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 75 ? '#10B981' :
    pct >= 50 ? '#F97316' :
                '#EF4444';

  return {
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 4,
        radius: '90%',
        center: ['50%', '62%'],
        axisLine: {
          lineStyle: {
            width: 12,
            color: [
              [pct / 100, color],
              [1, 'var(--border)'],
            ],
          },
        },
        axisTick:  { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        pointer:   { show: false },
        detail: {
          valueAnimation: true,
          formatter: `{value}%`,
          color: 'var(--card-foreground)',
          fontSize: 22,
          fontWeight: 700,
          offsetCenter: [0, '-10%'],
        },
        data: [{ value: pct, name: 'Face Quality' }],
        title: {
          offsetCenter: [0, '20%'],
          fontSize: 12,
          color: 'var(--muted-foreground)',
        },
      },
    ],
  };
}

// Main component
export default function SkinCharts({ profile }) {
  const { skin_type, conditions = [], skin_type_scores, condition_scores, face_quality_score } = profile;

  const allSkinTypes  = ['Oily', 'Dry', 'Combination', 'Normal', 'Sensitive'];
  const allConditions = ['Acne', 'Hyperpigmentation', 'Uneven tone', 'Dehydration', 'None detected'];

  const skinData = allSkinTypes.map((name) => ({
    name,
    value: skin_type_scores?.[name] ?? (name === skin_type ? profile.confidence : (1 - profile.confidence) / 4),
  }));

  const condData = allConditions.map((name) => ({
    name,
    value: condition_scores?.[name] ?? (conditions.includes(name) ? 0.65 : 0.15),
  }));

  const sectionTitle = {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--muted-foreground)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 8,
  };

  const card = {
    background: 'var(--card)',
    borderRadius: 12,
    border: '1px solid var(--border)',
    padding: '16px',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Section header */}
      <p style={{ ...sectionTitle, marginBottom: 0 }}>Detailed Breakdown</p>

      {/* Skin type vertical bar — rainfall style with toolbox + markPoint */}
      <div style={card}>
        <ReactECharts
          option={makeSkinTypeBarOption({ skinData, detectedType: skin_type })}
          style={{ height: 280 }}
          opts={{ renderer: 'svg' }}
        />
      </div>

      {/* Condition radar */}
      <div style={card}>
        <p style={sectionTitle}>Condition Radar</p>
        <ReactECharts
          option={makeRadarOption({ condData, selectedKeys: conditions })}
          style={{ height: 220 }}
          opts={{ renderer: 'svg' }}
        />
      </div>

      {/* Condition Nightingale rose */}
      <div style={card}>
        <p style={sectionTitle}>Condition Scores</p>
        <ReactECharts
          option={makeNightingaleOption({ condData, selectedKeys: conditions })}
          style={{ height: 320 }}
          opts={{ renderer: 'svg' }}
        />
      </div>

      {/* Face quality gauge (only if available) */}
      {face_quality_score != null && (
        <div style={{ ...card, textAlign: 'center' }}>
          <p style={sectionTitle}>Capture Quality</p>
          <ReactECharts
            option={makeGaugeOption(face_quality_score)}
            style={{ height: 160 }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      )}
    </div>
  );
}
