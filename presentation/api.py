from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from infrastructure.di_container import Container
from domain.exceptions import UnroutableQuery

app = FastAPI(title="Tribal Mapper")
container = Container()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    context_blocks: list[str]
    enriched_prompt: str


@app.post("/route", response_model=QueryResponse)
def route_query(request: QueryRequest) -> QueryResponse:
    try:
        result = container.route_query.execute(request.query)
    except UnroutableQuery as e:
        raise HTTPException(status_code=404, detail=str(e))
    return QueryResponse(
        context_blocks=result.context_blocks,
        enriched_prompt=result.enriched_prompt,
    )
