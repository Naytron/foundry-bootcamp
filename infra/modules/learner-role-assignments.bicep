targetScope = 'resourceGroup'

param foundryAccountName string
param foundryProjectName string
param searchServiceName string
param principalId string
param principalType string

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  name: foundryProjectName
  parent: foundryAccount
}

resource searchService 'Microsoft.Search/searchServices@2025-05-01' existing = {
  name: searchServiceName
}

var foundryUserRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '53ca6127-db72-4b80-b1b0-d745d6d5456d'
)
var searchServiceContributorRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
)
var searchIndexDataContributorRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
)

resource foundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryProject.id, principalId, foundryUserRoleDefinitionId)
  scope: foundryProject
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: foundryUserRoleDefinitionId
  }
}

resource searchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, searchServiceContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: searchServiceContributorRoleDefinitionId
  }
}

resource searchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, searchIndexDataContributorRoleDefinitionId)
  scope: searchService
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: searchIndexDataContributorRoleDefinitionId
  }
}
