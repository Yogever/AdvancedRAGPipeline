#BEEngineering/desing 
The system itself is a sort of implementation of [[LLM Frameworks#Data Layer]] and thus Data Layer Tools like [[LlamaIndex]] and [[LlamaHub]] will not be used.

However, For communicating with LLMs, using a framework at the [[LLM Frameworks#Application Layer]] would be a great fit. For that the main tool is [[LangChain]], which supplayes out-of-the-box tools to communication with AI models Including:
1. model abstraction/wrappers 
2. input to prompt template to request sending to result parsing
3. tool use (could be useful in the future)
