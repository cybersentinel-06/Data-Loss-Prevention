import { Shield, FileText, Database, AlertCircle } from 'lucide-react'

export default function Policies() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Policies</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage DLP policies and rules
        </p>
      </div>

      {/* Policy Info */}
      <div className="card bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <Shield className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-blue-900">YAML-Based Policy System</p>
            <p className="mt-1 text-sm text-blue-700">
              Policies are managed via YAML files on the server. Create policy files
              in <code className="bg-blue-100 px-1 py-0.5 rounded">/etc/cybersentinel/policies/</code>
            </p>
          </div>
        </div>
      </div>

      {/* Example Policies */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* PCI-DSS Policy */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-red-100 rounded-lg">
              <Shield className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">PCI-DSS Protection</h3>
              <p className="text-xs text-gray-500">policy-pci-001</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Status</span>
              <span className="badge badge-success">Enabled</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Severity</span>
              <span className="badge badge-danger">Critical</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Priority</span>
              <span className="font-medium">1</span>
            </div>
          </div>

          <p className="mt-4 text-sm text-gray-600">
            Detects and blocks credit card numbers (PAN) using pattern matching
            and Luhn validation. Triggers alerts and quarantine actions.
          </p>
        </div>

        {/* GDPR Policy */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Database className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">GDPR Compliance</h3>
              <p className="text-xs text-gray-500">policy-gdpr-001</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Status</span>
              <span className="badge badge-success">Enabled</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Severity</span>
              <span className="badge bg-orange-100 text-orange-800">High</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Priority</span>
              <span className="font-medium">2</span>
            </div>
          </div>

          <p className="mt-4 text-sm text-gray-600">
            Monitors for personally identifiable information (PII) including SSN,
            email addresses, and phone numbers.
          </p>
        </div>

        {/* HIPAA Policy */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <FileText className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">HIPAA Protection</h3>
              <p className="text-xs text-gray-500">policy-hipaa-001</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Status</span>
              <span className="badge badge-success">Enabled</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Severity</span>
              <span className="badge badge-danger">Critical</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Priority</span>
              <span className="font-medium">1</span>
            </div>
          </div>

          <p className="mt-4 text-sm text-gray-600">
            Protects protected health information (PHI) including medical record
            numbers and health insurance identifiers.
          </p>
        </div>

        {/* USB Device Policy */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <AlertCircle className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">USB Device Control</h3>
              <p className="text-xs text-gray-500">policy-usb-001</p>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Status</span>
              <span className="badge badge-success">Enabled</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Severity</span>
              <span className="badge bg-yellow-100 text-yellow-800">Medium</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Priority</span>
              <span className="font-medium">3</span>
            </div>
          </div>

          <p className="mt-4 text-sm text-gray-600">
            Monitors and logs all USB device connections. Generates alerts for
            unauthorized devices.
          </p>
        </div>
      </div>

      {/* Policy Creation Guide */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Creating New Policies</h3>

        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Create a new YAML file in <code className="bg-gray-100 px-1 py-0.5 rounded">/etc/cybersentinel/policies/</code>
          </p>

          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="text-xs overflow-x-auto">
              {`policy:
  id: policy-custom-001
  name: "My Custom Policy"
  enabled: true
  severity: high
  priority: 5
  stop_on_match: false

  rules:
    - id: rule-001
      name: "Detect API Keys"

      conditions:
        - field: content
          operator: regex
          value: '[A-Za-z0-9_-]{32,}'
        - field: event.type
          operator: equals
          value: file

      actions:
        - type: alert
          severity: high
          message: "Potential API key detected"
        - type: block
          enabled: true`}
            </pre>
          </div>

          <p className="text-sm text-gray-600">
            After creating a policy file, restart the manager service to load the new policy.
          </p>
        </div>
      </div>
    </div>
  )
}
