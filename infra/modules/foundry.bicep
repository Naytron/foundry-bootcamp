targetScope = 'resourceGroup'

param location string
param accountName string
param projectName string
param chatDeploymentName string
param chatModelName string
param chatModelVersion string
param chatDeploymentSku string
param chatDeploymentCapacity int
param embeddingDeploymentName string
param embeddingModelName string
param embeddingModelVersion string
param embeddingDeploymentSku string
param embeddingDeploymentCapacity int
param tags object = {}

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
  tags: tags
}

resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  name: chatDeploymentName
  parent: account
  sku: {
    name: chatDeploymentSku
    capacity: chatDeploymentCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatModelName
      version: chatModelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  name: embeddingDeploymentName
  parent: account
  sku: {
    name: embeddingDeploymentSku
    capacity: embeddingDeploymentCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: embeddingModelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
  dependsOn: [chatDeployment]
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: projectName
  parent: account
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'Microsoft Foundry AI development bootcamp project'
    displayName: 'Foundry Bootcamp project'
  }
  tags: tags
  dependsOn: [embeddingDeployment]
}

output accountName string = account.name
output projectName string = project.name
output projectEndpoint string = project.properties.endpoints['AI Foundry API']
output projectPrincipalId string = project.identity.principalId
