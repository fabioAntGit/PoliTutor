import * as memoryApi from "@/api/memory";

export const MemoryService = {
  listMemories: memoryApi.listMemories,
  deleteMemory: memoryApi.deleteMemory,
};
