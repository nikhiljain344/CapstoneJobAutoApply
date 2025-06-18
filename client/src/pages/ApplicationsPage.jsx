import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FileText, Calendar, Building, ExternalLink } from 'lucide-react'

export default function ApplicationsPage() {
  // Mock data for demonstration
  const mockApplications = [
    {
      id: 1,
      jobTitle: 'Senior Software Engineer',
      company: 'TechCorp Inc.',
      appliedDate: '2025-06-14',
      status: 'interview',
      method: 'api'
    },
    {
      id: 2,
      jobTitle: 'Frontend Developer',
      company: 'StartupXYZ',
      appliedDate: '2025-06-13',
      status: 'submitted',
      method: 'upload'
    },
    {
      id: 3,
      jobTitle: 'Full Stack Developer',
      company: 'DataCorp',
      appliedDate: '2025-06-12',
      status: 'pending',
      method: 'api'
    }
  ]

  const getStatusBadge = (status) => {
    const variants = {
      pending: 'secondary',
      submitted: 'default',
      interview: 'success',
      rejected: 'destructive',
      hired: 'success'
    }
    
    const labels = {
      pending: 'Pending',
      submitted: 'Submitted',
      interview: 'Interview',
      rejected: 'Rejected',
      hired: 'Hired'
    }

    return (
      <Badge variant={variants[status] || 'secondary'}>
        {labels[status] || status}
      </Badge>
    )
  }

  const getMethodBadge = (method) => {
    const labels = {
      api: 'API',
      upload: 'Upload',
      text: 'Text'
    }

    return (
      <Badge variant="outline">
        {labels[method] || method}
      </Badge>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Applications</h1>
        <p className="text-gray-600 mt-2">
          Track and manage your job applications.
        </p>
      </div>

      <div className="grid lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Application Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">47</div>
                <div className="text-sm text-blue-700">Total Applications</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">5</div>
                <div className="text-sm text-green-700">Interviews</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">85%</div>
                <div className="text-sm text-purple-700">Success Rate</div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Recent Applications</span>
              </CardTitle>
              <CardDescription>
                Your latest job applications and their status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockApplications.map((application) => (
                  <div key={application.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {application.jobTitle}
                        </h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                          <div className="flex items-center space-x-1">
                            <Building className="h-4 w-4" />
                            <span>{application.company}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-4 w-4" />
                            <span>{application.appliedDate}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(application.status)}
                          {getMethodBadge(application.method)}
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 text-center">
                <p className="text-gray-600 mb-4">
                  Full application tracking functionality will be implemented in Phase 6.
                </p>
                <Button variant="outline">
                  View All Applications
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

