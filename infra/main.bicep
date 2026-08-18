targetScope = 'subscription'

@description('Short azd environment name used to derive resource names.')
@minLength(1)
param environmentName string

@description('Azure region selected after model and service availability checks.')
param location string

@secure()
@description('Workshop access token stored as a Container Apps secret.')
param bootcampAccessToken string

@description('Object ID of the learner running azd provisioning.')
param learnerPrincipalId string

@description('Indicates whether azd found the Container App before provisioning.')
param appExists bool

@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
@description('Microsoft Entra principal type for the learner assignment.')
param learnerPrincipalType string = 'User'

@description('Azure AI Search SKU. Free is lowest cost; use basic when the subscription already has a free service.')
param searchSku string = 'free'

@description('Search index populated by the workshop seeding utility.')
param searchIndexName string = 'support-knowledge'

@description('Foundry chat deployment name exposed to the application.')
param chatDeploymentName string = 'gpt-4.1-mini'

@description('Chat model catalog name. Verify availability in the selected region before deployment.')
param chatModelName string = 'gpt-4.1-mini'

@description('Chat model version. Override when the selected region offers a different supported version.')
param chatModelVersion string = '2025-04-14'

@description('Chat deployment SKU.')
param chatDeploymentSku string = 'GlobalStandard'

@minValue(1)
@description('Chat deployment capacity in thousands of tokens per minute.')
param chatDeploymentCapacity int = 10

@description('Foundry embeddings deployment name exposed to the application.')
param embeddingDeploymentName string = 'text-embedding-3-small'

@description('Embeddings model catalog name.')
param embeddingModelName string = 'text-embedding-3-small'

@description('Embeddings model version.')
param embeddingModelVersion string = '1'

@description('Embeddings deployment SKU.')
param embeddingDeploymentSku string = 'Standard'

@minValue(1)
@description('Embeddings deployment capacity in thousands of tokens per minute.')
param embeddingDeploymentCapacity int = 10

var serviceName = 'app'
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var resourceGroupName = take('rg-${environmentName}-${resourceToken}', 90)
var foundryAccountName = 'fdry${resourceToken}'
var foundryProjectName = take('proj-${environmentName}-${resourceToken}', 64)
var searchServiceName = 'srch-${resourceToken}'
var containerRegistryName = 'cr${resourceToken}'
var logAnalyticsName = take('log-${environmentName}-${resourceToken}', 63)
var applicationInsightsName = take('appi-${environmentName}-${resourceToken}', 260)
var containerEnvironmentName = take('cae-${environmentName}-${resourceToken}', 60)
var containerAppName = take('ca-${environmentName}-${resourceToken}', 32)
var commonTags = {
  'azd-env-name': environmentName
  workload: 'foundry-bootcamp'
}

module resourceGroupModule 'br/public:avm/res/resources/resource-group:0.4.4' = {
  name: 'resource-group'
  params: {
    name: resourceGroupName
    location: location
    tags: commonTags
  }
}

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.16.1' = {
  name: 'log-analytics'
  scope: resourceGroup(resourceGroupName)
  params: {
    name: logAnalyticsName
    location: location
    dataRetention: 30
    skuName: 'PerGB2018'
    tags: commonTags
  }
  dependsOn: [resourceGroupModule]
}

module applicationInsights 'br/public:avm/res/insights/component:0.8.0' = {
  name: 'application-insights'
  scope: resourceGroup(resourceGroupName)
  params: {
    name: applicationInsightsName
    location: location
    applicationType: 'web'
    disableLocalAuth: false
    workspaceResourceId: logAnalytics.outputs.resourceId
    retentionInDays: 30
    tags: commonTags
  }
}

module foundry 'modules/foundry.bicep' = {
  name: 'foundry'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
    accountName: foundryAccountName
    projectName: foundryProjectName
    chatDeploymentName: chatDeploymentName
    chatModelName: chatModelName
    chatModelVersion: chatModelVersion
    chatDeploymentSku: chatDeploymentSku
    chatDeploymentCapacity: chatDeploymentCapacity
    embeddingDeploymentName: embeddingDeploymentName
    embeddingModelName: embeddingModelName
    embeddingModelVersion: embeddingModelVersion
    embeddingDeploymentSku: embeddingDeploymentSku
    embeddingDeploymentCapacity: embeddingDeploymentCapacity
    tags: commonTags
  }
  dependsOn: [resourceGroupModule]
}

module search 'br/public:avm/res/search/search-service:0.13.0' = {
  name: 'ai-search'
  scope: resourceGroup(resourceGroupName)
  params: {
    name: searchServiceName
    location: location
    sku: searchSku
    replicaCount: 1
    partitionCount: 1
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    tags: commonTags
  }
  dependsOn: [resourceGroupModule]
}

module containerRegistry 'br/public:avm/res/container-registry/registry:0.13.0' = {
  name: 'container-registry'
  scope: resourceGroup(resourceGroupName)
  params: {
    name: containerRegistryName
    location: location
    acrSku: 'Basic'
    acrAdminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleSetDefaultAction: 'Allow'
    tags: commonTags
  }
  dependsOn: [resourceGroupModule]
}

module containerEnvironment 'br/public:avm/res/app/managed-environment:0.15.0' = {
  name: 'container-apps-environment'
  scope: resourceGroup(resourceGroupName)
  params: {
    name: containerEnvironmentName
    location: location
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsWorkspaceResourceId: logAnalytics.outputs.resourceId
    }
    publicNetworkAccess: 'Enabled'
    zoneRedundant: false
    tags: commonTags
  }
}

resource existingContainerApp 'Microsoft.App/containerApps@2025-01-01' existing = if (appExists) {
  name: containerAppName
  scope: resourceGroup(resourceGroupName)
}

module containerApp 'br/public:avm/res/app/container-app:0.23.0' = {
  name: 'container-app'
  scope: resourceGroup(resourceGroupName)
  params: {
    name: containerAppName
    location: location
    environmentResourceId: containerEnvironment.outputs.resourceId
    managedIdentities: {
      systemAssigned: true
    }
    tags: union(commonTags, {
      'azd-service-name': serviceName
    })
    ingressExternal: true
    ingressAllowInsecure: false
    ingressTargetPort: 8000
    ingressTransport: 'http'
    activeRevisionsMode: 'Single'
    registries: [
      {
        server: containerRegistry.outputs.loginServer
        identity: 'system'
      }
    ]
    secrets: [
      {
        name: 'bootcamp-access-token'
        value: bootcampAccessToken
      }
      {
        name: 'application-insights-connection-string'
        value: applicationInsights.outputs.connectionString
      }
    ]
    containers: [
      {
        name: serviceName
        image: appExists
          ? existingContainerApp!.properties.template.containers[0].image
          : 'docker.io/traefik/whoami@sha256:200689790a0a0ea48ca45992e0450bc26ccab5307375b41c84dfc4f2475937ab'
        args: ['--port=8000']
        resources: {
          cpu: json('0.5')
          memory: '1Gi'
        }
        env: [
          { name: 'APP_ENV', value: 'production' }
          { name: 'USE_MOCK_SERVICES', value: 'false' }
          { name: 'FOUNDRY_PROJECT_ENDPOINT', value: foundry.outputs.projectEndpoint }
          { name: 'FOUNDRY_MODEL', value: chatDeploymentName }
          { name: 'EMBEDDING_MODEL', value: embeddingDeploymentName }
          { name: 'AZURE_AI_SEARCH_ENDPOINT', value: search.outputs.endpoint }
          { name: 'AZURE_AI_SEARCH_INDEX', value: searchIndexName }
          { name: 'AZURE_AI_SEARCH_SEMANTIC_CONFIGURATION', value: 'support-semantic-config' }
          { name: 'AZURE_AI_SEARCH_VECTOR_FIELD', value: 'content_vector' }
          { name: 'EMBEDDING_DIMENSIONS', value: '1536' }
          { name: 'AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING', value: 'true' }
          { name: 'OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT', value: 'false' }
          { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', secretRef: 'application-insights-connection-string' }
          { name: 'BOOTCAMP_ACCESS_TOKEN', secretRef: 'bootcamp-access-token' }
        ]
        probes: [
          {
            type: 'Startup'
            httpGet: { path: '/health', port: 8000 }
            initialDelaySeconds: 1
            periodSeconds: 3
            timeoutSeconds: 2
            failureThreshold: 30
          }
          {
            type: 'Liveness'
            httpGet: { path: '/health', port: 8000 }
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          }
          {
            type: 'Readiness'
            httpGet: { path: '/ready', port: 8000 }
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
            successThreshold: 1
          }
        ]
      }
    ]
    scaleSettings: {
      minReplicas: 0
      maxReplicas: 1
      rules: [
        {
          name: 'workshop-http'
          http: {
            metadata: {
              concurrentRequests: '10'
            }
          }
        }
      ]
    }
  }
}

module monitoringRoleAssignments 'modules/monitoring-role-assignments.bicep' = {
  name: 'monitoring-role-assignments'
  scope: resourceGroup(resourceGroupName)
  params: {
    applicationInsightsName: applicationInsights.outputs.name
    logAnalyticsWorkspaceName: logAnalytics.outputs.name
    foundryProjectPrincipalId: foundry.outputs.projectPrincipalId
    learnerPrincipalId: learnerPrincipalId
    learnerPrincipalType: learnerPrincipalType
  }
}

module foundryApplicationInsightsConnection 'modules/foundry-application-insights-connection.bicep' = {
  name: 'foundry-application-insights-connection'
  scope: resourceGroup(resourceGroupName)
  params: {
    foundryAccountName: foundry.outputs.accountName
    foundryProjectName: foundry.outputs.projectName
    applicationInsightsResourceId: applicationInsights.outputs.resourceId
    applicationInsightsConnectionString: applicationInsights.outputs.connectionString
  }
  dependsOn: [monitoringRoleAssignments]
}

module learnerRoleAssignments 'modules/learner-role-assignments.bicep' = {
  name: 'learner-role-assignments'
  scope: resourceGroup(resourceGroupName)
  params: {
    foundryAccountName: foundry.outputs.accountName
    foundryProjectName: foundry.outputs.projectName
    searchServiceName: search.outputs.name
    principalId: learnerPrincipalId
    principalType: learnerPrincipalType
  }
}

module runtimeRoleAssignments 'modules/runtime-role-assignments.bicep' = {
  name: 'runtime-role-assignments'
  scope: resourceGroup(resourceGroupName)
  params: {
    foundryAccountName: foundry.outputs.accountName
    foundryProjectName: foundry.outputs.projectName
    searchServiceName: search.outputs.name
    principalId: containerApp.outputs.systemAssignedMIPrincipalId!
  }
}

// A separate deployment breaks the identity/registry dependency cycle for AcrPull.
module acrPull 'modules/acr-pull-role-assignment.bicep' = {
  name: 'container-app-acr-pull'
  scope: resourceGroup(resourceGroupName)
  params: {
    registryName: containerRegistry.outputs.name
    principalId: containerApp.outputs.systemAssignedMIPrincipalId!
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroupName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output FOUNDRY_PROJECT_ENDPOINT string = foundry.outputs.projectEndpoint
output FOUNDRY_MODEL string = chatDeploymentName
output EMBEDDING_MODEL string = embeddingDeploymentName
output AZURE_AI_SEARCH_ENDPOINT string = search.outputs.endpoint
output AZURE_AI_SEARCH_INDEX string = searchIndexName
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.outputs.connectionString
output SERVICE_URL string = 'https://${containerApp.outputs.fqdn}'
