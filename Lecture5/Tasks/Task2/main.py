import json
from urllib.request import urlopen, Request
from urllib.parse import quote_plus
import argparse
import boto3
import uuid
from dotenv import load_dotenv

headers = {
    'user-agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
}


def analytics(api_response):
    stats = {
        "total_quotes": 0,
        "authors": {},
        "tags": {}
    }

    quotes = api_response.get("data", [])

    for index, quote in enumerate(quotes):
        stats["total_quotes"] += 1

        author_name = quote["author"]["name"]
        if author_name not in stats["authors"]:
            stats["authors"][author_name] = {
                "quote_indexes": [index],
                "quotes_available": 1
            }
        else:
            stats["authors"][author_name]["quote_indexes"].append(index)
            stats["authors"][author_name]["quotes_available"] += 1

        for tag in quote.get("tags", []):
            tag_name = tag["name"]
            if tag_name not in stats["tags"]:
                stats["tags"][tag_name] = {
                    "quote_indexes": [index],
                    "quotes_with_tag": 1
                }
            else:
                stats["tags"][tag_name]["quote_indexes"].append(index)
                stats["tags"][tag_name]["quotes_with_tag"] += 1

    return stats


def aws_s3_client_init():
    load_dotenv()


def init_client():
    load_dotenv()
    client = boto3.client(
        "s3",
        aws_access_key_id=getenv("aws_access_key_id"),
        aws_secret_access_key=getenv("aws_secret_access_key"),
        aws_session_token=getenv("aws_session_token"),
        region_name=getenv("aws_region_name")
    )
    # check if credentials are correct
    client.list_buckets()

    return client

def save_to_s3(aws_s3_client, bucket_name, quote_obj):
    filename = f"{uuid.uuid4()}.json"
    aws_s3_client.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=json.dumps(quote_obj, indent=2),
        ContentType="application/json"
    )
    print(f"✅ Quote saved to s3://{bucket_name}/{filename}")


def main():
    args = parser.parse_args()

    if args.inspire:
        if isinstance(args.inspire, str):
            author_encoded = quote_plus(args.inspire)
            url = f"https://api.quotable.kurokeita.dev/api/quotes/random?author={author_encoded}"
        else:
            url = "https://api.quotable.kurokeita.dev/api/quotes/random"

        with urlopen(Request(url, headers=headers)) as response:
            json_result = json.loads(response.read().decode())
            quote = json_result.get("quote", {})
            content = quote.get("content")
            author = quote.get("author", {}).get("name")

            if content and author:
                print(f'🗨 "{content}" — {author}')

                # Save to S3 if --save flag is provided
                if args.save:
                    aws_s3_client = init_client()
                    save_to_s3(aws_s3_client, args.bucket_name, quote)
            else:
                print("No quote found for the given author.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CLI program that helps with S3 buckets and inspiration quotes.",
        prog='main.py'
    )
    parser.add_argument(
        'bucket_name',
        help="Name of the S3 bucket to save quotes to (if --save is used)"
    )
    parser.add_argument(
        '-i',
        '--inspire',
        nargs='?',
        const=True,
        help="Returns a random quote or a quote by a specific author"
    )
    parser.add_argument(
        '-s',
        '--save',
        action='store_true',
        help="If provided, saves the quote to the given S3 bucket"
    )

    main()
