# IEX Ingestion

Service to routinely query IEX Cloud for the latest data and store it in S3.

## Setup

You need the [Serverless Framework](https://github.com/serverless/serverless) CLI installed to deploy this ingestion service. It's a good idea to install this globally:

```sh
npm install --global serverless
```

The extensions used by this service also need to be installed:

```sh
npm install
```

## Deploy

Make sure your AWS credentials are [configured correctly](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) so that they can be used to deploy the service.

In addition, the following environment variables must be set:

- `IEX_S3_BUCKET`: Name of the S3 bucket used to store data.
- `IEX_S3_PREFIX`: S3 "directory" prefix (with trailing `/`) to store metadata and ingested files in.
- `IEX_ENDPOINT`: IEX API endpoint to use.
- `IEX_TOKEN`: IEX security token to validate requests with.
- `IEX_ROLE`: IAM role name for the service to execute with.

To deploy the service, run:

```sh
serverless deploy
```

This will deploy all resources required by the service. To undeploy, run:

```sh
serverless remove
```

## Scripts

The `scripts/` directory contains helper scripts for various infrequent operations:

- `./scripts/clear_raw` will clear all "raw" JSON files in S3.
- `./scripts/process_files` will find and process any "raw" JSON files without
  corresponding Parquet files.

## Development

For local development and testing, you can create a conda environment to mimic the Lambda runtime:

```sh
make env
```

The Python source files can be formatted with:

```sh
make format
```

## S3 Structure

Files in S3 related to this service are organized as follows:

```
s3://
└── {IEX_S3_BUCKET}
    └── {IEX_S3_PREFIX}
            ├── definitions.json
            ├── raw/
            │   └── chart/
            │       ├── key_1/
            │       ├── ...
            │       └── key_n/
            └── processed/
                ├── key_1/
                ├── ...
                └── key_n/
```

Each `key_n/` folder contains API responses related to that key in `definitions.json` for that stage. The raw responses are stored as files named `{YYYYMMDDhhmmss}.csv` based on the time of the request. The processed responses are stored as `{YYYYMMDDhhmmss}.parquet` files corresponding to the timestamps of the original raw files.
