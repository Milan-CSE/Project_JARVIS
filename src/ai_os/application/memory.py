from __future__ import annotations
from ai_os.cognition.memory import MemoryStore
from ai_os.intelligence.context import IntelligenceContext, ContextItem
from ai_os.intelligence.context.source import ContextSource
class MemoryDrivenAssistant:
    """13.3 enriches application context from Memory; it does not own MemoryStore."""
    def __init__(self, memory: MemoryStore):
        if not isinstance(memory, MemoryStore): raise TypeError('memory must implement MemoryStore')
        self._memory=memory
    def enrich(self, context: IntelligenceContext, *, limit: int = 10) -> IntelligenceContext:
        if not isinstance(context, IntelligenceContext): raise TypeError('context must be IntelligenceContext')
        if not isinstance(limit,int) or isinstance(limit,bool) or limit<=0: raise ValueError('limit must be positive int')
        items=self._memory.query(str(context.input), limit=limit)
        enriched=list(context.items)
        for item in items:
            enriched.append(ContextItem(kind='memory', source=ContextSource.MEMORY, value=item.content, metadata={'item_id':item.item_id,'source':item.source}))
        return IntelligenceContext(input=context.input, identity=context.identity, items=tuple(enriched), constraints=context.constraints, metadata=context.metadata)
