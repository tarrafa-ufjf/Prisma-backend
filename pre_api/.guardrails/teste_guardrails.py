from guardrails import Guard
from guardrails.hub import DetectPII

guard = Guard().use(
    DetectPII()
)

result = guard.validate(
    "O email do aluno é joao@gmail.com"
)

print(result)