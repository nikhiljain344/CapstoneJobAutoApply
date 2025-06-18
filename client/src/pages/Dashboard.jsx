import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

const Dashboard = () => {
  const { user } = useAuth()
  const [dashboardStats, setDashboardStats] = useState(null)
  const [applicationTrends, setApplicationTrends] = useState([])
  const [successMetrics, setSuccessMetrics] = useState(null)
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      // Fetch dashboard stats
      const statsResponse = await fetch('http://localhost:5002/api/analytics/dashboard-stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        setDashboardStats(statsData.stats)
      }

      // Fetch application trends
      const trendsResponse = await fetch('http://localhost:5002/api/analytics/application-trends?days=30', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (trendsResponse.ok) {
        const trendsData = await trendsResponse.json()
        setApplicationTrends(trendsData.trends)
      }

      // Fetch success metrics
      const metricsResponse = await fetch('http://localhost:5002/api/analytics/success-metrics', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json()
        setSuccessMetrics(metricsData.metrics)
      }

      // Fetch performance insights
      const insightsResponse = await fetch('http://localhost:5002/api/analytics/performance-insights', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (insightsResponse.ok) {
        const insightsData = await insightsResponse.json()
        setInsights(insightsData.insights)
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const StatCard = ({ title, value, subtitle, trend, color = 'blue' }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
        {trend && (
          <div className={`text-sm font-medium ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '↗' : '↘'} {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  )

  const ProgressBar = ({ label, current, target, color = 'blue' }) => {
    const percentage = Math.min((current / target) * 100, 100)
    return (
      <div className="mb-4">
        <div className="flex justify-between text-sm font-medium text-gray-700 mb-1">
          <span>{label}</span>
          <span>{current}/{target}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`bg-${color}-600 h-2 rounded-full transition-all duration-300`}
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <div className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}% complete</div>
      </div>
    )
  }

  const InsightCard = ({ insight }) => {
    const getInsightColor = (type) => {
      switch (type) {
        case 'success': return 'green'
        case 'warning': return 'yellow'
        case 'error': return 'red'
        default: return 'blue'
      }
    }

    const color = getInsightColor(insight.type)
    
    return (
      <div className={`bg-white rounded-lg shadow-md p-4 border-l-4 border-${color}-500`}>
        <h4 className={`font-semibold text-${color}-800 mb-2`}>{insight.title}</h4>
        <p className="text-gray-600 text-sm mb-2">{insight.message}</p>
        {insight.action && (
          <p className={`text-${color}-600 text-sm font-medium`}>💡 {insight.action}</p>
        )}
      </div>
    )
  }

  const TrendChart = ({ data }) => {
    if (!data || data.length === 0) return <div className="text-gray-500">No data available</div>

    const maxValue = Math.max(...data.map(d => d.total))
    
    return (
      <div className="space-y-2">
        {data.slice(-7).map((day, index) => (
          <div key={day.date} className="flex items-center space-x-3">
            <div className="w-16 text-xs text-gray-500">
              {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </div>
            <div className="flex-1 bg-gray-200 rounded-full h-4 relative">
              <div 
                className="bg-blue-500 h-4 rounded-full flex items-center justify-end pr-2"
                style={{ width: `${(day.total / maxValue) * 100}%` }}
              >
                <span className="text-xs text-white font-medium">{day.total}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.name || 'Job Seeker'}! 👋
          </h1>
          <p className="text-gray-600 mt-2">Here's your job application progress and insights</p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'analytics', label: 'Analytics' },
              { id: 'insights', label: 'Insights' },
              { id: 'goals', label: 'Goals' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && dashboardStats && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Total Applications"
                value={dashboardStats.overview.total_applications}
                subtitle="All time"
                color="blue"
              />
              <StatCard
                title="Success Rate"
                value={`${dashboardStats.overview.success_rate}%`}
                subtitle={`${dashboardStats.overview.successful_applications} successful`}
                color="green"
              />
              <StatCard
                title="This Week"
                value={dashboardStats.time_based.applications_this_week}
                subtitle="Applications sent"
                color="purple"
              />
              <StatCard
                title="Queue Status"
                value={dashboardStats.queue.total_queued}
                subtitle={`${dashboardStats.queue.pending} pending`}
                color="orange"
              />
            </div>

            {/* Profile Completion */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Completion</h3>
              <ProgressBar
                label="Profile Completeness"
                current={dashboardStats.overview.profile_completion}
                target={100}
                color="green"
              />
              <p className="text-sm text-gray-600">
                Complete your profile to get better job matches and improve your application success rate.
              </p>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
              {dashboardStats.recent_activity.length > 0 ? (
                <div className="space-y-3">
                  {dashboardStats.recent_activity.map((activity, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">Job Application</p>
                        <p className="text-sm text-gray-600">
                          {new Date(activity.applied_at).toLocaleDateString()} • {activity.application_method}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        activity.status === 'submitted' ? 'bg-green-100 text-green-800' :
                        activity.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {activity.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No recent activity. Start applying to jobs!</p>
              )}
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-8">
            {/* Application Trends */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Trends (Last 7 Days)</h3>
              <TrendChart data={applicationTrends} />
            </div>

            {/* Success Metrics */}
            {successMetrics && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Methods</h3>
                  <div className="space-y-3">
                    {Object.entries(successMetrics.application_methods).map(([method, stats]) => (
                      <div key={method} className="flex items-center justify-between">
                        <span className="text-gray-700 capitalize">{method}</span>
                        <div className="text-right">
                          <div className="text-sm font-medium">{stats.success_rate.toFixed(1)}%</div>
                          <div className="text-xs text-gray-500">{stats.successful}/{stats.total}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Best Days to Apply</h3>
                  <div className="space-y-3">
                    {Object.entries(successMetrics.best_performing_days)
                      .sort((a, b) => b[1].success_rate - a[1].success_rate)
                      .map(([day, stats]) => (
                      <div key={day} className="flex items-center justify-between">
                        <span className="text-gray-700">{day}</span>
                        <div className="text-right">
                          <div className="text-sm font-medium">{stats.success_rate.toFixed(1)}%</div>
                          <div className="text-xs text-gray-500">{stats.successful}/{stats.total}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Insights Tab */}
        {activeTab === 'insights' && (
          <div className="space-y-8">
            {/* AI Insights */}
            {successMetrics?.insights && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {successMetrics.insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}

            {/* Optimization Suggestions */}
            {insights?.optimization_suggestions && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization Suggestions</h3>
                <div className="space-y-4">
                  {insights.optimization_suggestions.map((suggestion, index) => (
                    <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <h4 className="font-semibold text-blue-900 mb-2">{suggestion.title}</h4>
                      <p className="text-blue-800 text-sm mb-2">{suggestion.description}</p>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        suggestion.priority === 'high' ? 'bg-red-100 text-red-800' :
                        suggestion.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {suggestion.priority} priority
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skill Recommendations */}
            {insights?.skill_recommendations && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Skills</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {insights.skill_recommendations.map((skill, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900">{skill.skill}</h4>
                      <p className="text-sm text-gray-600">{skill.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Goals Tab */}
        {activeTab === 'goals' && insights?.goal_tracking && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Goal</h3>
                <ProgressBar
                  label="Applications This Week"
                  current={insights.goal_tracking.weekly.progress}
                  target={insights.goal_tracking.weekly.goal}
                  color="blue"
                />
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Goal</h3>
                <ProgressBar
                  label="Applications This Month"
                  current={insights.goal_tracking.monthly.progress}
                  target={insights.goal_tracking.monthly.goal}
                  color="green"
                />
              </div>
            </div>

            {/* Goal Setting */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Set Your Goals</h3>
              <p className="text-gray-600 mb-4">
                Setting realistic goals helps you stay motivated and track your progress effectively.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Weekly Application Goal
                  </label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="12"
                    min="1"
                    max="50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Monthly Application Goal
                  </label>
                  <input
                    type="number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="50"
                    min="1"
                    max="200"
                  />
                </div>
              </div>
              <button className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                Update Goals
              </button>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="p-4 bg-blue-50 rounded-lg border border-blue-200 hover:bg-blue-100 transition-colors text-left">
              <h4 className="font-medium text-blue-900">Find Job Matches</h4>
              <p className="text-sm text-blue-700">Get AI-powered job recommendations</p>
            </button>
            <button className="p-4 bg-green-50 rounded-lg border border-green-200 hover:bg-green-100 transition-colors text-left">
              <h4 className="font-medium text-green-900">Upload Resume</h4>
              <p className="text-sm text-green-700">Update your resume for better matches</p>
            </button>
            <button className="p-4 bg-purple-50 rounded-lg border border-purple-200 hover:bg-purple-100 transition-colors text-left">
              <h4 className="font-medium text-purple-900">View Queue</h4>
              <p className="text-sm text-purple-700">Manage your application queue</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

