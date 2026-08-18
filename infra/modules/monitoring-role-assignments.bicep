targetScope = 'resourceGroup'

param applicationInsightsName string
param logAnalyticsWorkspaceName string
param foundryProjectPrincipalId string
param learnerPrincipalId string
param learnerPrincipalType string

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2025-07-01' existing = {
  name: logAnalyticsWorkspaceName
}

var monitoringMetricsPublisherRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '3913510d-42f4-4e42-8a64-420c390055eb'
)
var logAnalyticsReaderRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '73c42c96-874c-492b-b04d-ab87d138a893'
)

resource projectMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, foundryProjectPrincipalId, monitoringMetricsPublisherRoleDefinitionId)
  scope: applicationInsights
  properties: {
    principalId: foundryProjectPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: monitoringMetricsPublisherRoleDefinitionId
  }
}

resource projectApplicationInsightsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, foundryProjectPrincipalId, logAnalyticsReaderRoleDefinitionId)
  scope: applicationInsights
  properties: {
    principalId: foundryProjectPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: logAnalyticsReaderRoleDefinitionId
  }
}

resource projectWorkspaceReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(logAnalyticsWorkspace.id, foundryProjectPrincipalId, logAnalyticsReaderRoleDefinitionId)
  scope: logAnalyticsWorkspace
  properties: {
    principalId: foundryProjectPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: logAnalyticsReaderRoleDefinitionId
  }
}

resource learnerApplicationInsightsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, learnerPrincipalId, logAnalyticsReaderRoleDefinitionId)
  scope: applicationInsights
  properties: {
    principalId: learnerPrincipalId
    principalType: learnerPrincipalType
    roleDefinitionId: logAnalyticsReaderRoleDefinitionId
  }
}

resource learnerWorkspaceReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(logAnalyticsWorkspace.id, learnerPrincipalId, logAnalyticsReaderRoleDefinitionId)
  scope: logAnalyticsWorkspace
  properties: {
    principalId: learnerPrincipalId
    principalType: learnerPrincipalType
    roleDefinitionId: logAnalyticsReaderRoleDefinitionId
  }
}
