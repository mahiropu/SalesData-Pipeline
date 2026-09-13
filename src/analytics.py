from src import warehouse
from src.utils import load_config, resolve


def split_queries(sql_text):
    queries = []
    for chunk in sql_text.split(";"):
        chunk = chunk.strip()
        if chunk:
            queries.append(chunk)
    return queries


def main():
    config = load_config()
    connection = warehouse.connect(config)

    with open(resolve("sql/analytics_queries.sql")) as f:
        queries = split_queries(f.read())

    for i, query in enumerate(queries, start=1):
        df = connection.execute(query).df()

        print(f"\n=== Query {i} ===")
        if df.empty:
            print("(no rows)")
        else:
            print(df.to_string(index=False))

    print("\n=== File processing log here ===")
    log = connection.execute("SELECT * FROM processed_files ORDER BY file_name").df()
    print(log.to_string(index=False))

    connection.close()


if __name__ == "__main__":
    main()
