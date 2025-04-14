#!/usr/bin/env python3

import argparse
import sys

import boto3
from botocore.exceptions import ClientError, ParamValidationError

"""
    Check to see if a AWS SSM Parameter exists
    If it does not exist, create it
    If it does exist, check to see if the value is up to date and update it if not

    Returns:
        Status of the operation
"""

parser = argparse.ArgumentParser(description="Check for AWS SSM Parameter")

parser.add_argument("--name", type=str, help="AWS SSM Parameter Name")
parser.add_argument("--value", type=str, default=None, help="AWS SSM Parameter Value")
parser.add_argument("--description", type=str, default="", help="AWS SSM Parameter Description")
parser.add_argument("--tier", type=str, default="Standard", help="The parameter tier to assign to a parameter.")
parser.add_argument("--type", type=str, default="String", help="AWS SSM Parameter Type")
parser.add_argument("--file-path", type=str, default=None, help="File to read the value from")

args = parser.parse_args()


def get_parameter_value(parameter_value: str | None, file_path: str | None) -> str:
    """
    Get parameter value from either the provided value or a file.

    Parameters:
        parameter_value (str): The parameter value.
        file_path (str): The file path to read the value from.

    Returns:
        str: The parameter value.
    """

    if parameter_value is None and file_path is None:
        print("Either parameter_value or file_path must be provided")
        sys.exit(1)

    if parameter_value is not None and file_path is not None:
        print("Warning: Both parameter_value and file_path are provided, file_path will be prioritized")

    try:
        if file_path:
            with open(file_path, "r") as file:
                parameter_value = file.read()
        else:
            parameter_value = args.value
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)

    if parameter_value is None or parameter_value == "":
        print("Parameter value or provided file path cannot be empty")
        sys.exit(1)

    return parameter_value


def check_value_ssm_parameter(
    parameter_name: str,
    parameter_description: str,
    parameter_value: str | None = None,
    parameter_tier: str | None = "Standard",
    parameter_type: str | None = "String",
    file_path: str | None = None,
) -> bool:
    """
    Check to see if the value of a AWS SSM Parameter is up to date

    URLs:
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.describe_parameters # noqa
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter

    Parameters:
        parameter_name (str): AWS SSM Parameter Name
        parameter_value (str): AWS SSM Parameter Value
        parameter_description (str): Optional AWS SSM Parameter Description
        parameter_tier (str): Optional The parameter tier to assign to a parameter.
        parameter_type (str): Optional AWS SSM Parameter Type
        file_path (str): Optional file to read the value from

    Returns:
        True or False (bool): [Value of the SSM parameter for the client token]
    """

    parameter_value = get_parameter_value(parameter_value, file_path)

    ssm = boto3.client("ssm")

    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        value = response["Parameter"]["Value"]
        print("Parameter Exists, checking parameter details....")
        print(f" - Parameter Value: {parameter_name}")

        response = ssm.describe_parameters(
            ParameterFilters=[
                {"Key": "Name", "Values": [parameter_name]},
            ],
        )

        parameter_details = response["Parameters"][0]

        try:
            description = parameter_details["Description"]
        except KeyError:
            print("Description not found")
            description = ""

        tier = parameter_details["Tier"]
        remote_type = parameter_details["Type"]

        if remote_type != parameter_type:
            raise ValueError(f"Cannot change parameter type from {remote_type} to {parameter_type}")
        elif value == parameter_value and description == parameter_description and tier == parameter_tier:
            print(" - Verified parameter details are current.")
            return True
        else:
            print(" - Parameter details need to be updated.")
            return False
    except ClientError as e:
        # If the parameter does not exist, return None
        if e.response["Error"]["Code"] == "ParameterNotFound":
            print("Parameter does not exist and needs to be created.")
            return False
        else:
            raise


def put_ssm_parameter(
    parameter_name: str,
    parameter_description: str = "",
    parameter_value: str | None = None,
    parameter_tier: str = "Standard",
    parameter_type: str = "String",
    file_path: str | None = None,
) -> bool:
    """
    Create or Update a AWS SSM Parameter

    URLs:
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter

    Parameters:
        parameter_name (str): AWS SSM Parameter Name
        parameter_value (str): AWS SSM Parameter Value
        parameter_description (str): Optional AWS SSM Parameter Description
        parameter_tier (str): Optional The parameter tier to assign to a parameter.
        parameter_type (str): Optional AWS SSM Parameter Type
        file_path (str): Optional file to read the value from

    Returns:
        True or False (bool): [Value of the SSM parameter for the client token]
    """

    parameter_value = get_parameter_value(parameter_value, file_path)

    ssm = boto3.client("ssm")

    try:
        ssm.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Description=parameter_description,
            Type=parameter_type,
            Overwrite=True,
            Tier=parameter_tier,
            DataType="text",
        )
        print(" - Parameter successfully created/updated.")
        return True
    except ParamValidationError as e:
        print(e)
        return False
    except ClientError as e:
        match e.response["Error"]["Code"]:
            case "ParameterLimitExceeded":
                message = (
                    "Parameter Limit Exceeded\n"
                    "Parameter Store API calls can't exceed the maximum allowed API request rate per account and per Region.\n"  # noqa
                    "https://docs.aws.amazon.com/general/latest/gr/ssm.html"
                )
                print(message)
                return False
            case "InvalidAllowedPatternException":
                message = (
                    "Invalid Allowed Pattern\n"
                    "https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_PutParameter.html#API_PutParameter_RequestSyntax"  # noqa
                )
                print(message)
                return False
            case "TooManyUpdates":
                print("There are concurrent updates for a resource that supports one update at a time.")
                return False
            case _:
                raise


value_response = check_value_ssm_parameter(
    parameter_name=args.name,
    parameter_value=args.value,
    parameter_description=args.description,
    parameter_tier=args.tier,
    parameter_type=args.type,
    file_path=args.file_path,
)

if value_response is False:
    # value needs to be updated
    put_ssm_parameter(
        parameter_name=args.name,
        parameter_value=args.value,
        parameter_description=args.description,
        parameter_tier=args.tier,
        parameter_type=args.type,
        file_path=args.file_path,
    )
