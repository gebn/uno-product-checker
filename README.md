# Uno Product Checker

[![Build Status](https://travis-ci.org/gebn/uno-product-checker.svg?branch=master)](https://travis-ci.org/gebn/uno-product-checker)

This script checks which products of a specific type (e.g. *Phone & Broadband*)
are available on a line, and publishes a message to an SNS topic if this list
differs from a preconfigured "known" set. It is designed to run in
[AWS Lambda](https://aws.amazon.com/lambda/) on an infrequent schedule - please
don't use this to bombard Uno. Their API caches responses until midnight each
day, so there is little point in querying more than once every 24 hours, at an
absolute maximum.

## Configuration

Uno's API is hosted in Reading, so eu-west-2 or eu-west-1/eu-central-1 are the
best AWS regions from a latency perspective (however, given the check takes >10
seconds, this is arguably negligible).

| Parameter | Value                   |
|-----------|-------------------------|
| Runtime   | Python 3.6              |
| Handler   | `main.lambda_handler`   |
| Memory    | 128 MiB (only uses ~32) |
| Timeout   | 45 seconds              |

## Environment Variables

The function expects the following to be defined:

| Name                     | Description                                                                                                                                                                   |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PHONE_NUMBER`           | The phone number on the line to check, without spaces or country code.                                                                                                        |
| `PRODUCT_TYPE`           | The package within which to query for products, e.g. Phone & Broadband is *phone_broadband*.                                                                                  |
| `EXPECTED_PRODUCTS`      | A comma separated list of product IDs that are known to be available on the line, e.g. Talk Surf would be *133,134,135*.                                                      |
| `NOTIFICATION_TOPIC_ARN` | The SNS topic to publish to, should the list of actual products differ from the list of varied products. See `uno_product_checker/main.py` for the structure.                 |
| `PUSHOVER_APP_TOKEN`     | The [Pushover](https://pushover.net/) application token to send notifications as. This assumes something sending notifications via Pushover is a consumer on the above topic. |
