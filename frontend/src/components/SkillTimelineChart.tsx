import React, { useMemo, useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getSkillActivity, SkillActivityItem, SkillActivityResponse } from '../api/intelligence';

interface Props {
  initialInterval?: 'month' | 'year';
}

const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088fe',
  '#00c49f', '#ffbb28', '#ff8042', '#a4de6c', '#d0ed57'
];

interface ChartDataPoint {
  period: string;
  [key: string]: string | number;
}

/**
 * スキル成熟度グラフコンポーネント。
 * GitHub のアクティビティに基づいたスキルの成長を折れ線グラフで表示します。
 */
export const SkillTimelineChart: React.FC<Props> = ({ initialInterval = 'month' }) => {
  const [data, setData] = useState<SkillActivityItem[]>([]);
  const [interval, setInterval] = useState<'month' | 'year'>(initialInterval);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  // アクティビティデータを取得
  const fetchActivity = async (currentInterval: 'month' | 'year') => {
    setLoading(true);
    setError(null);
    try {
      const response: SkillActivityResponse = await getSkillActivity(currentInterval);
      setData(response.skills);
      // 合計アクティビティが多い上位 5 スキルをデフォルトで表示
      const topSkills = [...response.skills]
        .sort((a, b) => 
          b.timeline.reduce((sum, p) => sum + p.activity, 0) - 
          a.timeline.reduce((sum, p) => sum + p.activity, 0)
        )
        .slice(0, 5)
        .map(s => s.skill);
      setSelectedSkills(topSkills);
    } catch (err) {
      setError('アクティビティの取得に失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivity(interval);
  }, [interval]);

  // Recharts 用にデータを変換
  const chartData = useMemo(() => {
    if (data.length === 0) return [];

    // 全てのユニークな期間（月/年）を取得してソート
    const periods = Array.from(new Set(
      data.flatMap(s => s.timeline.map(p => p.period))
    )).sort();

    // Recharts 形式に変換: [{ period: '2023-01', Python: 4, FastAPI: 2 }, ...]
    return periods.map(period => {
      const point: ChartDataPoint = { period };
      data.forEach(s => {
        if (selectedSkills.includes(s.skill)) {
          const activity = s.timeline.find(p => p.period === period)?.activity || 0;
          point[s.skill] = activity;
        }
      });
      return point;
    });
  }, [data, selectedSkills]);

  if (loading) return <div>読み込み中...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div style={{ width: '100%', padding: '20px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>スキル成熟度グラフ</h3>
        <div>
          <button 
            onClick={() => setInterval('month')}
            style={{ 
              padding: '4px 12px', 
              background: interval === 'month' ? '#007bff' : '#f8f9fa',
              color: interval === 'month' ? 'white' : 'black',
              border: '1px solid #dee2e6',
              borderRadius: '4px 0 0 4px',
              cursor: 'pointer'
            }}
          >
            月
          </button>
          <button 
            onClick={() => setInterval('year')}
            style={{ 
              padding: '4px 12px', 
              background: interval === 'year' ? '#007bff' : '#f8f9fa',
              color: interval === 'year' ? 'white' : 'black',
              border: '1px solid #dee2e6',
              borderRadius: '0 4px 4px 0',
              cursor: 'pointer'
            }}
          >
            年
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {data.map((s) => (
          <label key={s.skill} style={{ 
            display: 'flex', 
            alignItems: 'center', 
            fontSize: '12px', 
            background: selectedSkills.includes(s.skill) ? '#e9ecef' : 'transparent',
            padding: '2px 8px',
            borderRadius: '12px',
            border: '1px solid #dee2e6',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={selectedSkills.includes(s.skill)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedSkills([...selectedSkills, s.skill]);
                } else {
                  setSelectedSkills(selectedSkills.filter(sk => sk !== s.skill));
                }
              }}
              style={{ marginRight: '4px' }}
            />
            {s.skill}
          </label>
        ))}
      </div>

      <div style={{ height: '400px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis />
            <Tooltip />
            <Legend />
            {selectedSkills.map((skill, index) => (
              <Line
                key={skill}
                type="monotone"
                dataKey={skill}
                stroke={COLORS[index % COLORS.length]}
                activeDot={{ r: 8 }}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
