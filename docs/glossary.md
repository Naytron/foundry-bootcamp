# Glossary

**Agent Framework**  
Microsoft's SDK for building agents and controlled workflows across model providers.

**Agent session**  
Conversation state reused across messages. This workshop keeps the session in process.

**Azure AI Search**  
Azure retrieval service used for keyword, semantic, vector, and hybrid search.

**Citation**  
Structured source metadata kept separate from generated text.

**Context**  
Reference information supplied for one model invocation. It is not automatically memory.

**Embedding**  
A numeric vector representing text for similarity search.

**Ephemeral agent**  
An agent whose instructions and tools live in application code rather than a persisted server-side agent definition.

**Evaluation dataset**  
Versioned prompts and expected behaviors used to measure quality and safety.

**Foundry account**  
Azure management boundary for projects, model deployments, tools, identity, networking, and policy.

**Foundry project**  
Project-scoped endpoint and isolation boundary for models, agents, tools, data, and observability.

**Grounding**  
Retrieving relevant external information and supplying it as evidence for generation.

**Hybrid search**  
A retrieval query that combines text/semantic ranking with vector similarity.

**Managed identity**  
Microsoft Entra identity managed by Azure for passwordless service-to-service access.

**Prompt injection**  
Untrusted content that attempts to override an agent's intended instructions.

**Responses API**  
Project-scoped OpenAI-compatible API used by the capstone for model and tool orchestration.

**Tool**  
A typed function or hosted capability the model may request. Application code remains responsible for authorization and execution.

**Trace**  
OpenTelemetry spans that describe request, model, retrieval, and tool execution.

