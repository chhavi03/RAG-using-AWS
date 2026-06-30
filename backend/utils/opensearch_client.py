from opensearchpy import OpenSearch

def get_opensearch_client():
    client = OpenSearch(
        hosts=[{
            "host": "search-rag-opensearch-fk3z7zosbdmhznnoauhhyeskay.aos.ap-south-1.on.aws",   # without https
            "port": 443
        }],
        http_auth=("admin", "Admin@123"),
        use_ssl=True,
        verify_certs=False
    )
    return client