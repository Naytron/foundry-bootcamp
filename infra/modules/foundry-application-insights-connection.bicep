targetScope = 'resourceGroup'

param foundryAccountName string
param foundryProjectName string
param applicationInsightsResourceId string

@secure()
param applicationInsightsConnectionString string

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-09-01' existing = {
  name: foundryAccountName
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-09-01' existing = {
  name: foundryProjectName
  parent: foundryAccount
}

resource applicationInsightsConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-09-01' = {
  name: 'application-insights'
  parent: foundryProject
  properties: {
    category: 'AppInsights'
    target: applicationInsightsResourceId
    #disable-next-line BCP036
    authType: 'ProjectManagedIdentity'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: applicationInsightsResourceId
      ApplicationInsightsConnectionString: applicationInsightsConnectionString
    }
  }
}
