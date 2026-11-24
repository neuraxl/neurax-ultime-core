from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    max_output_tokens: int = Field(default=1200, ge=64, le=2000)


class ProviderResult(BaseModel):
    provider: str
    model: str
    status: str
    response: str | None = None
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None


class ArbitrationResult(BaseModel):
    provider: str
    model: str
    status: str
    synthesis: str | None = None
    latency_ms: int
    error: str | None = None


class CompareResponse(BaseModel):
    trace_id: str
    status: str
    successful_providers: int
    results: list[ProviderResult]
    arbitration: ArbitrationResult | None
    disclaimer: str = (
        "Model agreement is not proof of truth. Verify important claims against "
        "independent evidence; provider outputs may contain errors."
    )
