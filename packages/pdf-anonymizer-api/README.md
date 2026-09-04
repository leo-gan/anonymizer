# PDF Anonymizer HTTP service

A thin FastAPI wrapper around `pdf-anonymizer-core`. It does **not** depend on the CLI. There is no authentication.

```bash
pip install pdf-anonymizer-api
pdf-anonymizer-api --host 127.0.0.1 --port 8000
```

Docker files live in this package. From the repository root:

```bash
docker compose -f packages/pdf-anonymizer-api/docker-compose.yml up --build
```

Docs: [HTTP service and Docker](https://leo-gan.github.io/anonymizer/project/http-service/).
